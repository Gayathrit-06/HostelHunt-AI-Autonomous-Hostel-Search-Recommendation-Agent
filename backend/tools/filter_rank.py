import re

def filter_and_rank_hostels(results: list[dict], user_query: str) -> list[dict]:
    query_lower = user_query.lower()

    number_match = re.search(r'\b(\d+)\b', user_query)
    requested_count = int(number_match.group(1)) if number_match else 3
    requested_count = max(1, min(requested_count, 10))

    is_ladies_only = any(term in query_lower for term in ["ladies", "women", "female", "girls"])
    is_gents_only = any(term in query_lower for term in ["gents", "men", "male", "boys"])

    # Expanded junk patterns for OTAs, aggregators, and generic headings
    junk_patterns = [
        r'top\s*\d*', r'best\s*\d*', r'list\s*of', r'choose\s*from', r'hostels?\s*with', r'hostels?\s*in',
        r'orbitz', r'expedia', r'hostelworld', r'hotels\.com', r'booking\.com', r'agoda', r'tripadvisor',
        r'justdial', r'magicbricks', r'quikr', r'yellowpages', r'webindia', r'makemytrip', r'goibibo',
        r'paying\s*guest', r'dorms\.com', r'free\s*cancellation', r'student\s*accommodation',
        r'girls\s*hostel', r'boys\s*hostel', r'youth\s*hostel'
    ]

    filtered = []
    seen_names = set()

    for item in results:
        raw_title = item.get("title", "").strip()
        content = item.get("content", "").strip()[:180].replace("\n", " ")
        source_url = item.get("url", "").lower()
        combined_text = f"{raw_title} {content}".lower()

        # 1. Skip item completely if source URL comes from an aggregator/OTA
        if any(re.search(p, source_url) for p in junk_patterns):
            continue

        # 2. Gender filtering
        if is_ladies_only and any(m in combined_text for m in ["mens hostel", "gents pg", "boys hostel"]):
            continue
        if is_gents_only and any(w in combined_text for w in ["ladies hostel", "women pg", "girls hostel"]):
            continue

        # 3. Extract candidate names
        matches = re.findall(
            r'([A-Z][a-zA-Z0-9\s\'\.\-]{2,}(?:Hostel|PG|Inn|Residency|Stay|Accommodations))', 
            content + " " + raw_title
        )

        clean_name = ""
        for cand in matches:
            cand_clean = cand.strip()
            cand_lower = cand_clean.lower()

            # Skip candidate if it matches any generic junk pattern
            if any(re.search(p, cand_lower) for p in junk_patterns) or len(cand_clean) < 5:
                continue

            clean_name = cand_clean
            break

        if not clean_name:
            continue

        clean_name = re.sub(r'^\d+\s*', '', clean_name)

        if clean_name.lower() in seen_names:
            continue
        seen_names.add(clean_name.lower())

        filtered.append({
            "name": clean_name,
            "content": content,
            "url": item.get("url", ""),
            "distance": item.get("distance", "Nearby target area")
        })

        if len(filtered) == requested_count:
            break

    return filtered