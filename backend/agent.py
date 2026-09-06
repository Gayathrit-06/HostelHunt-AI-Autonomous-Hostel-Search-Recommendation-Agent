import os
import operator
import re
import urllib.parse
from typing_extensions import TypedDict, Annotated

import googlemaps
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph import StateGraph, START, END

try:
    from backend.config import GPLACES_API_KEY
except ModuleNotFoundError:
    from config import GPLACES_API_KEY

# Import tools from the local tools directory
try:
    from backend.tools.web_search import search_tavily_web          
    from backend.tools.filter_rank import filter_and_rank_hostels   
    from backend.tools.distance_calculator import compute_distance  
except ModuleNotFoundError:
    from tools.web_search import search_tavily_web          
    from tools.filter_rank import filter_and_rank_hostels   
    from tools.distance_calculator import compute_distance


# ------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------
def convert_dollars_to_rupees(text: str) -> str:
    """Replaces $XX with calculated ₹ INR amounts and removes any leftover $ signs."""
    if not text:
        return ""
        
    def replace_dollars(match):
        try:
            usd_val = float(match.group(1))
            inr_val = int(usd_val * 83)  # Approximate exchange rate
            return f"₹{inr_val:,}"
        except ValueError:
            return ""

    text = re.sub(r'\$\s*(\d+(?:\.\d+)?)', replace_dollars, text)
    return text.replace("$", "₹")


def sanitize_location_suffix(query: str) -> str:
    """
    Dynamically extracts ANY place, city, or area from the prompt.
    Removes hardcoded checks so all locations are parsed correctly.
    """
    query_clean = query.strip()

    # 1. Match prepositions like "in", "near", "around", "at", "opposite" followed by location text
    prep_match = re.search(
        r'\b(?:in|near|around|at|opposite|close to)\s+([a-zA-Z0-9\s,-]+)', 
        query_clean, 
        re.IGNORECASE
    )
    
    if prep_match:
        raw_loc = prep_match.group(1)
        # Strip trailing filters like budget, gender, or hostel keywords
        stop_words = r'\b(under|below|budget|cheap|gents|ladies|mens|womens|girls|boys|rs|rupees|month|k|hostel|hostels|pg)\b.*'
        clean_loc = re.sub(stop_words, '', raw_loc, flags=re.IGNORECASE).strip()
        if clean_loc:
            return clean_loc.title()

    # 2. Fallback: Clean standard query filler and constraint words
    filter_words = r'\b(find|search|show|get|hostels?|pg|gents|ladies|mens|womens|girls|boys|under|below|budget|cheap|for|near|in|around|rs|rupees|month|k)\b'
    cleaned = re.sub(filter_words, '', query_clean, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b\d+\b', '', cleaned).strip()

    return cleaned.title() if cleaned else "Chennai"


def extract_clean_amenities(raw_text: str) -> str:
    """Extracts genuine amenity keywords from web snippets."""
    if not raw_text:
        return "Wi-Fi, Power Backup, Food Options, Housekeeping"
    
    found_amenities = []
    text_lower = raw_text.lower()
    
    if any(k in text_lower for k in ["wifi", "wi-fi", "internet"]):
        found_amenities.append("Wi-Fi")
    if any(k in text_lower for k in ["food", "mess", "cooking", "meal", "breakfast", "dinner"]):
        found_amenities.append("Food Options")
    if "ac" in text_lower or "air condition" in text_lower:
        found_amenities.append("AC Rooms")
    if any(k in text_lower for k in ["power", "backup", "generator"]):
        found_amenities.append("Power Backup")
    if any(k in text_lower for k in ["security", "cctv"]):
        found_amenities.append("24/7 Security & CCTV")
    if any(k in text_lower for k in ["laundry", "housekeeping", "washing"]):
        found_amenities.append("Housekeeping & Laundry")

    return ", ".join(found_amenities) if found_amenities else "Wi-Fi, Power Backup, Food Options, Housekeeping"


def extract_dynamic_rent(content_text: str, user_query: str) -> str:
    """Extracts actual prices from snippet content or user constraints formatted in INR."""
    found_prices = re.findall(r'₹?\s*(\d{1,2}[,\.]?\d{3})', content_text)
    
    clean_prices = []
    for price in found_prices:
        val = int(price.replace(',', '').replace('.', ''))
        if 2000 <= val <= 25000:
            clean_prices.append(val)

    if clean_prices:
        min_p = min(clean_prices)
        max_p = max(clean_prices)
        return f"₹{min_p:,}/month" if min_p == max_p else f"₹{min_p:,} – ₹{max_p:,}/month"

    # Fallback to user budget constraints (e.g., handles "8000k", "8k", "under 10000")
    k_match = re.search(r'\b(\d+)\s*k\b', user_query.lower())
    if k_match:
        val = int(k_match.group(1))
        max_b = val if val > 1000 else val * 1000
        return f"₹{max(2000, max_b - 2000):,} – ₹{max_b:,}/month"

    budget_numbers = re.findall(r'\b\d{4,5}\b', user_query)
    if budget_numbers:
        max_b = int(budget_numbers[0])
        return f"₹{max(2000, max_b - 2000):,} – ₹{max_b:,}/month"

    return "₹4,000 – ₹7,000/month"


# ------------------------------------------------------------------
# Agent State Definition
# ------------------------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    error: str | None


# ------------------------------------------------------------------
# Graph Nodes
# ------------------------------------------------------------------
# Updated google_places_node snippet incorporating distance computation
def google_places_node(state: AgentState):
    query = state["messages"][-1].content
    try:
        if not GPLACES_API_KEY:
            raise Exception("Google Places API Key missing.")

        target_location = sanitize_location_suffix(query)
        search_query = f"hostels in {target_location}"

        gmaps = googlemaps.Client(key=GPLACES_API_KEY)
        places_result = gmaps.places(query=search_query)
        results = places_result.get("results", [])

        if not results:
            raise Exception(f"No places found for {target_location} via Google Places API.")

        formatted_places = []
        rent_str = extract_dynamic_rent("", query)

        for idx, p in enumerate(results[:5], start=1):
            name = p.get("name", f"Hostel Option {idx}").title()
            vicinity = p.get("formatted_address") or p.get("vicinity") or f"Accessible to {target_location}"

            # Calculate distance using your local distance_calculator tool
            distance_str = "N/A"
            try:
                # Computes distance between the hostel and the main target location/landmark
                dist_res = compute_distance(origin=vicinity, destination=target_location)
                if isinstance(dist_res, dict) and "distance" in dist_res:
                    distance_str = dist_res["distance"]
                elif isinstance(dist_res, str):
                    distance_str = dist_res
            except Exception:
                distance_str = f"Near {target_location}"

            dest_param = urllib.parse.quote(f"{name} {target_location}")
            dir_url = f"https://www.google.com/maps/dir/?api=1&destination={dest_param}"

            block = (
                f"{idx}. **{name}**\n"
                f"Location: {vicinity}\n"
                f"Distance: {distance_str} to central {target_location}\n"
                f"Rent: {rent_str}\n"
                f"Amenities: Wi-Fi, Power Backup, Food Options, Housekeeping\n"
                f"🗺️ Directions: [Google Maps Directions]({dir_url})"
            )
            formatted_places.append(block)

        content = convert_dollars_to_rupees("\n\n".join(formatted_places))
        return {"messages": [AIMessage(content=content)], "error": None}

    except Exception as e:
        return {"error": str(e)}


def tavily_fallback_node(state: AgentState):
    """Fallback node executing web search when Google Places API fails."""
    user_query = state["messages"][-1].content

    try:
        target_location = sanitize_location_suffix(user_query)
        search_term = f"hostels in {target_location}"
        
        raw_results = search_tavily_web(search_term)
        ranked_hostels = filter_and_rank_hostels(results=raw_results, user_query=search_term)

        if not ranked_hostels:
            return {"messages": [AIMessage(content=f"No specific hostels matching your criteria were found in {target_location}.")], "error": None}

        formatted = []
        for idx, item in enumerate(ranked_hostels[:5], start=1):
            raw_content = item.get("content", "")
            raw_title = item.get("title", "")
            raw_name = item.get("name", "")

            # Properly extract and clean real hostel names from titles or web snippets
            source_name = raw_name if raw_name else raw_title
            if source_name:
                clean_name = re.split(r'[-|:,]', source_name)[0].strip().title()
            else:
                clean_name = f"Hostel Option {idx}"

            rent_display = extract_dynamic_rent(raw_content, user_query)
            amenities_display = extract_clean_amenities(raw_content)

            dest_param = urllib.parse.quote(f"{clean_name} {target_location}")
            directions_url = f"https://www.google.com/maps/dir/?api=1&destination={dest_param}"

            block = (
                f"{idx}. **{clean_name}**\n"
                f"Location: Accessible to {target_location}\n"
                f"Rent: {rent_display}\n"
                f"Amenities: {amenities_display}\n"
                f"🗺️ Directions: [Google Maps Directions]({directions_url})"
            )
            formatted.append(block)

        return {"messages": [AIMessage(content="\n\n".join(formatted))], "error": None}

    except Exception as tavily_err:
        return {"messages": [AIMessage(content=f"Error: Fallback search failed ({tavily_err})")], "error": None}


def route_after_google(state: AgentState):
    if state.get("error"):
        return "tavily_fallback"
    return END


# ------------------------------------------------------------------
# Build Graph
# ------------------------------------------------------------------
builder = StateGraph(AgentState)
builder.add_node("google_places", google_places_node)
builder.add_node("tavily_fallback", tavily_fallback_node)

builder.add_edge(START, "google_places")
builder.add_conditional_edges("google_places", route_after_google)
builder.add_edge("tavily_fallback", END)

agent_executor = builder.compile()