"""
Tavily Search Tool — Real-time web research for ICP pain points and market data.
"""
import json
from datetime import datetime
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from rich.console import Console

from config.settings import settings

console = Console()


class TavilyTool:
    """Tavily search API wrapper with result processing."""

    BASE_URL = "https://api.tavily.com/search"

    def __init__(self):
        import requests
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
    )
    def search(
        self,
        query: str,
        max_results: int = 10,
        include_raw_content: bool = False,
        days: int = 30,
    ) -> dict:
        """
        Execute a Tavily search and return structured results.

        Args:
            query: Search query string
            max_results: Number of results to return
            include_raw_content: Include full page content
            days: Only results from last N days

        Returns:
            Dict with answer, results list, and metadata
        """
        payload = {
            "api_key": settings.TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": include_raw_content,
            "topic": "finance",
        }

        response = self._session.post(self.BASE_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def search_trading_pain_points(self) -> dict:
        """Search for current pain points of retail traders."""
        queries = [
            "retail traders biggest problems losing money 2024 2025",
            "why do traders fail trading psychology mistakes",
            "trading signals services pain points reviews",
        ]
        results = {}
        for q in queries:
            console.print(f"  [cyan]→ Tavily:[/cyan] {q[:60]}...")
            try:
                data = self.search(q, max_results=5)
                results[q] = {
                    "answer": data.get("answer", ""),
                    "sources": [
                        {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content", "")[:300]}
                        for r in data.get("results", [])[:5]
                    ],
                }
                console.print(f"  [green]✓[/green] Got answer + {len(results[q]['sources'])} sources")
            except Exception as e:
                console.print(f"  [yellow]⚠ Search failed: {e}[/yellow]")
                results[q] = {"answer": "", "sources": []}
        return results

    def search_crowd_wisdom_positioning(self) -> dict:
        """Research crowd intelligence trading services and positioning."""
        queries = [
            "crowd intelligence trading signals services comparison 2025",
            "social trading platforms success rates crowd wisdom investing",
            "collective intelligence stock market outperform individual traders",
        ]
        results = {}
        for q in queries:
            console.print(f"  [cyan]→ Tavily:[/cyan] {q[:60]}...")
            try:
                data = self.search(q, max_results=5)
                results[q] = {
                    "answer": data.get("answer", ""),
                    "sources": [
                        {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content", "")[:300]}
                        for r in data.get("results", [])[:5]
                    ],
                }
                console.print(f"  [green]✓[/green] Got {len(results[q]['sources'])} sources")
            except Exception as e:
                console.print(f"  [yellow]⚠ Search failed: {e}[/yellow]")
                results[q] = {"answer": "", "sources": []}
        return results

    def search_icp_profile(self, icp: str = "retail traders") -> dict:
        """Research the Ideal Customer Profile in depth."""
        query = f"{icp} daily habits trading routine pain frustrations 2025"
        console.print(f"  [cyan]→ Tavily ICP Research:[/cyan] {query[:60]}...")
        try:
            data = self.search(query, max_results=8, include_raw_content=True)
            return {
                "answer": data.get("answer", ""),
                "sources": data.get("results", [])[:6],
                "searched_at": datetime.now().isoformat(),
            }
        except Exception as e:
            console.print(f"  [yellow]⚠ ICP search failed: {e}[/yellow]")
            return {"answer": "", "sources": [], "searched_at": datetime.now().isoformat()}

    def extract_insights(self, search_results: dict) -> dict:
        """Aggregate search results into marketing insights."""
        all_text = []
        for query, data in search_results.items():
            if data.get("answer"):
                all_text.append(data["answer"])
            for src in data.get("sources", []):
                if src.get("snippet"):
                    all_text.append(src["snippet"])

        return {
            "raw_text": "\n---\n".join(all_text),
            "source_count": sum(len(d.get("sources", [])) for d in search_results.values()),
            "queries_run": list(search_results.keys()),
        }


# Singleton
tavily_tool = TavilyTool()
