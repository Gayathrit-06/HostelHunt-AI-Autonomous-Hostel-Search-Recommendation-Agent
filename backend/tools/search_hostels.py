import os
import googlemaps
from langchain_community.tools.tavily_search import TavilySearchResults

# Initialize Tavily search tool as a fallback
tavily_search = TavilySearchResults(max_results=3)

def search_google_places(query: str) -> str:
    """Searches Google Places for hostels. Automatically falls back to Tavily Web Search if Google Places fails."""
    gplaces_key = os.getenv("GPLACES_API_KEY")
    
    # Attempt Primary Tool: Google Places API
    try:
        if not gplaces_key:
            raise ValueError("GPLACES_API_KEY missing.")

        gmaps = googlemaps.Client(key=gplaces_key)
        places_result = gmaps.places(query=f"hostels near {query}")
        
        results = places_result.get('results', [])
        if not results:
            raise ValueError("No places found via Google Places.")

        formatted_places = []
        for p in results[:3]:
            formatted_places.append(
                f"- Name: {p.get('name')}, Address: {p.get('vicinity')}, Rating: {p.get('rating', 'N/A')}★"
            )
        return "\n".join(formatted_places)

    except Exception as e:
        print(f"\n[Tool Notice]: Google Places failed ({e}). Executing Tavily Search fallback...\n")
        
        # Execute Fallback Tool: Tavily Search
        try:
            web_results = tavily_search.invoke({"query": f"top student hostels and PGs near {query}"})
            
            formatted_web = ["(Retrieved via Tavily Web Search Fallback):"]
            for r in web_results:
                formatted_web.append(f"- {r.get('content')[:200]}... (Source: {r.get('url')})")
            
            return "\n".join(formatted_web)

        except Exception as tavily_err:
            return f"Error: Both Google Places and Tavily fallback failed. ({tavily_err})"