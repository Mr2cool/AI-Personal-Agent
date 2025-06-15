# WARNING: This file is deprecated and not used in the current app.
# All ADK/vertexai/Tool code is obsolete and should be removed.
# You can safely delete this file or leave it as a stub.

import os
import requests

# Example: Add a Wikipedia tool (dummy, replace with real implementation if needed)
def wikipedia_tool(query):
    url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(" ", "_")}'
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get('extract', 'No summary found.')
    except requests.RequestException as e:
        return f'Wikipedia error: {e}'

class BrightDataSearchTool:
    def __call__(self, query: str) -> str:
        api_key = os.getenv("BRIGHTDATA_API_KEY")
        dataset_id = os.getenv("BRIGHTDATA_DATASET_ID")
        if not api_key or not dataset_id:
            return "Bright Data API credentials are not set."
        url = f"https://api.brightdata.com/dca/{dataset_id}"
        payload = {"query": query}
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            return f"Bright Data API error: {e}"

brightdata_tool = BrightDataSearchTool()

def query_agent(user_query):
    """Send a query to the tools and return the response."""
    # Example: Try Bright Data first, fallback to Wikipedia
    result = brightdata_tool(user_query)
    if "error" in result.lower() or "credentials" in result.lower():
        return wikipedia_tool(user_query)
    return result
