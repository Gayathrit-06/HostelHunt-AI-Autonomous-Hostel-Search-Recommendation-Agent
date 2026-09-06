import re

def compute_distance(origin: str, destination: str) -> str:
    """
    Extracts explicit distance numbers (e.g., '1.2 km') from snippet text,
    or returns a fallback location label.
    """
    text_to_search = f"{origin} {destination}"
    dist_match = re.search(r'(\d+(?:\.\d+)?\s*(?:km|meters|m))\s*(?:from|away|near)?', text_to_search, re.IGNORECASE)
    
    if dist_match:
        return dist_match.group(1)
    return "Nearby target area"