from duckduckgo_search import DDGS
from langsmith import traceable


class WebSearch:
    @traceable(run_type="tool")
    def search(self, query: str, max_results: int = 5) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if not results:
                    return ""
                lines = []
                for r in results:
                    title = r.get("title", "")
                    body = r.get("body", "")
                    if title and body:
                        lines.append(f"- {title}: {body}")
                    elif body:
                        lines.append(f"- {body}")
                return "\n".join(lines[:max_results])
        except Exception:
            return ""
