from langchain_tavily import TavilySearch

def search_tavily_web(query: str, max_results: int = 8) -> list[dict]:
    """
    Executes a web search via Tavily and returns a list of raw result dicts.
    """
    tavily = TavilySearch(max_results=max_results)
    raw_results = tavily.invoke({"query": query})
    
    if isinstance(raw_results, dict):
        return raw_results.get("results", [])
    elif isinstance(raw_results, list):
        return raw_results
    return []