from dotenv import load_dotenv, find_dotenv
from tavily import TavilyClient
from langchain.tools import tool

load_dotenv(find_dotenv())

client = TavilyClient()


def tavily_serach(query: str):
    """this tool is specialized in researching
    Args:
    query : str, the topic to search for ."""

    response = client.search(query=query, max_result=5)

    reuslts = []

    for i, r in enumerate(response["results"], 1):
        title = r.get("title", "Unknown")
        url = r.get("url", "")
        snippet = r.get("content", "")

        if len(snippet) > 300:
            snippet = snippet[:300].rsplit()

        reuslts.append(f"""URL:{url}
Title:{title}
Content:{snippet}""")

    return "\n\n".join(reuslts)
