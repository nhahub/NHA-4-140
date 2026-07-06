import asyncio
import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class DuckDuckGoSearch:

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
                    url = r.get("href", "")
                    if title and body:
                        lines.append(f"- {title}: {body} ({url})")
                    elif body:
                        lines.append(f"- {body}")
                return "\n".join(lines[:max_results])
        except Exception as e:
            logger.warning("DuckDuckGo search failed for query '%s': %s", query, e)
            return ""

    async def search_prices(self, make: str, model: str, year: int) -> list[dict]:
        queries = [
            f"{make} {model} {year} price Egypt EGP",
            f"{make} {model} {year} سعر مصر",
            f"{make} {model} {year} للبيع مصر سعر",
            f"site:olx.com.eg {make} {model} {year}",
            f"site:contactcars.com {make} {model} {year}",
            f"{make} {model} {year} market value Egypt used car price",
            f"{make} {model} {year} price in Egypt otlob hatla2nee contact",
        ]

        loop = asyncio.get_running_loop()

        async def _run(q: str) -> dict:
            snippets = await loop.run_in_executor(None, self.search, q, 8)
            return {"query": q, "snippets": snippets}

        results = await asyncio.gather(*[_run(q) for q in queries])
        return results
