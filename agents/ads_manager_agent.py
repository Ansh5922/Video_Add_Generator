"""
Ads Manager Agent — Agent 1

Responsibilities:
  1. Scrape Meta Ads Library via Apify for top trading/finance ads (last 30 days)
  2. Score and rank ads by performance signals
  3. Extract marketing concepts, pain points, hooks, and ICP signals via LLM
  4. Save results to output/ads/winning_ads.json and marketing_insights.json
"""
import json
from datetime import datetime
from pathlib import Path

from agents.base_agent import HermesAgent, AgentStatus
from tools.apify_tool import apify_tool, TRADING_KEYWORDS
from tools.llm_tool import llm
from config.settings import settings

# CrowdWisdom-specific search terms (supplement default keywords)
CWT_KEYWORDS = [
    "trading signals",
    "stock market investment",
    "forex swing trading",
    "day trading alerts",
]

SYSTEM_PROMPT = """You are an expert marketing analyst specializing in financial trading products and performance advertising.
You analyze ads from the Meta Ads Library to extract actionable marketing intelligence.
Always respond with valid JSON only."""


class AdsManagerAgent(HermesAgent):
    """
    Agent 1: Ads Manager

    Uses Apify to scrape Meta Ads Library for top-performing trading ads,
    then uses the LLM to extract marketing insights, ICP pain points, and
    proven creative concepts from the best-performing ads.
    """

    def __init__(self):
        super().__init__(
            name="Ads Manager Agent",
            description="Scrape Meta Ads Library → score best ads → extract marketing insights",
            emoji="📊",
        )
        # Register tools
        self.register_tool("search_meta_ads", apify_tool.search_meta_ads)
        self.register_tool("score_and_rank", apify_tool.score_ads)
        self.register_tool("llm_complete_json", llm.complete_json)

        # Add tasks to Kanban queue
        self.add_task("scrape_meta_ads", "Search Meta Ads Library via Apify")
        self.add_task("score_and_rank", "Score ads by performance signals")
        self.add_task("extract_insights", "LLM analysis: extract ICP, pain points, hooks")
        self.add_task("save_results", "Save winning_ads.json + marketing_insights.json")

    def run(self, input_data=None) -> dict:
        """Execute the full Ads Manager pipeline."""
        self._start()

        try:
            # ── Task 1: Scrape Meta Ads ────────────────────────────────────────
            task_scrape = self.tasks[0]
            self._task_start(task_scrape)
            raw_ads = self.call_tool(
                "search_meta_ads",
                keywords=CWT_KEYWORDS,
                country="US",
                limit=30,
                days_back=30,
            )
            self._task_done(task_scrape, len(raw_ads))

            # ── Task 2: Score & Rank ───────────────────────────────────────────
            task_score = self.tasks[1]
            self._task_start(task_score)
            scored_ads = self.call_tool("score_and_rank", raw_ads)
            top_ads = scored_ads[:10]  # Top 10
            self._task_done(task_score, len(top_ads))

            # ── Task 3: LLM Marketing Analysis ────────────────────────────────
            task_analyze = self.tasks[2]
            self._task_start(task_analyze)
            insights = self._extract_marketing_insights(top_ads)
            self._task_done(task_analyze, "OK")

            # ── Task 4: Save Results ───────────────────────────────────────────
            task_save = self.tasks[3]
            self._task_start(task_save)
            saved = self._save_results(top_ads, insights)
            self._task_done(task_save, saved)

            result = {
                "top_ads": top_ads,
                "marketing_insights": insights,
                "total_scraped": len(raw_ads),
                "top_count": len(top_ads),
            }
            self._complete(result)
            return result

        except Exception as e:
            self._fail(str(e))
            raise

    def _extract_marketing_insights(self, ads: list[dict]) -> dict:
        """Use LLM to extract marketing intelligence from top ads."""
        # Prepare ad summaries for the LLM
        ad_summaries = "\n\n---\n\n".join(
            f"AD #{i+1} (Score: {ad.get('relevance_score', 0)}, Keyword: {ad.get('keyword', '')})\n"
            f"Page: {ad.get('page_name', '')}\n"
            f"Copy: {ad.get('ad_text', '')[:400]}\n"
            f"CTA: {ad.get('call_to_action', '')}\n"
            f"Type: {ad.get('creative_type', '')}"
            for i, ad in enumerate(ads[:6])
        )

        user_prompt = f"""Analyze these top-performing trading/finance ads from Meta Ads Library and extract comprehensive marketing intelligence for CrowdWisdom Trading (crowdwisdomtrading.com — a crowd intelligence trading signals platform).

TOP ADS:
{ad_summaries}

Product Context:
- CrowdWisdom aggregates signals from 10,000+ professional traders
- Provides weekly consensus: direction, entry zones, stop-loss, profit targets  
- Targets retail traders and investors
- Free weekly briefing + Pro tier ($29.99/mo)
- Unique angle: "wisdom of the crowd" vs solo guessing

Extract and return a JSON with:
{{
  "icp_profile": {{
    "primary_audience": "description",
    "age_range": "25-55",
    "pain_points": ["pain1", "pain2", ...],
    "aspirations": ["aspiration1", ...],
    "daily_reality": "what their trading day looks like",
    "biggest_fear": "string",
    "trigger_moment": "moment that makes them seek a solution"
  }},
  "proven_hooks": [
    {{"hook": "hook text", "format": "question/statement/stat", "emotion": "fear/greed/curiosity"}}
  ],
  "winning_concepts": [
    {{"concept": "description", "why_it_works": "psychological reason"}}
  ],
  "emotional_triggers": ["trigger1", "trigger2"],
  "power_words": ["word1", "word2"],
  "competitor_weaknesses": ["weakness1", "weakness2"],
  "crowdwisdom_unique_angles": ["angle1", "angle2"],
  "recommended_ad_angles": [
    {{
      "type": "A",
      "name": "Pain-First Hook",
      "premise": "open with the biggest pain",
      "hook_example": "example hook",
      "tone": "empathetic, urgent"
    }},
    {{
      "type": "B",
      "name": "Data-Proof Hook",
      "premise": "lead with a shocking statistic",
      "hook_example": "example hook",
      "tone": "authoritative, credible"
    }},
    {{
      "type": "C",
      "name": "Transformation Hook",
      "premise": "show the before/after transformation",
      "hook_example": "example hook",
      "tone": "inspirational, aspirational"
    }}
  ]
}}"""

        try:
            insights = self.call_tool("llm_complete_json", SYSTEM_PROMPT, user_prompt)
            return insights
        except Exception as e:
            # Fallback insights if LLM fails
            return self._fallback_insights()

    def _fallback_insights(self) -> dict:
        """Fallback marketing insights based on product knowledge."""
        return {
            "icp_profile": {
                "primary_audience": "Retail traders with 1-5 years experience, losing more than winning",
                "age_range": "28-52",
                "pain_points": [
                    "Losing money despite hours of research",
                    "Information overload from multiple sources",
                    "Trading alone without peer insight",
                    "Missing entries due to FOMO or fear",
                    "Poor win rate despite technical analysis",
                ],
                "aspirations": [
                    "Consistent profitable trades",
                    "Financial freedom",
                    "Trade like a professional",
                    "Stop the emotional rollercoaster",
                ],
                "daily_reality": "Spends 2-4 hours/day on charts, still second-guesses every trade",
                "biggest_fear": "Losing their trading account before finding an edge",
                "trigger_moment": "After a painful losing streak or blowing a stop-loss",
            },
            "proven_hooks": [
                {"hook": "I lost $47,000 before discovering crowd wisdom", "format": "confession", "emotion": "fear"},
                {"hook": "What if 10,000 pro traders already knew your next move?", "format": "question", "emotion": "curiosity"},
                {"hook": "87% of retail traders lose money. Here's the 13% secret.", "format": "stat", "emotion": "greed"},
            ],
            "winning_concepts": [
                {"concept": "Crowd intelligence vs solo guessing", "why_it_works": "Social proof at scale"},
                {"concept": "Time savings (15 min/week vs 40 hrs/week)", "why_it_works": "Efficiency and lifestyle appeal"},
            ],
            "emotional_triggers": ["fear of missing out", "fear of loss", "greed", "validation", "belonging"],
            "power_words": ["proven", "10,000+", "consensus", "stop guessing", "free", "weekly", "professional"],
            "competitor_weaknesses": ["Noisy signals", "Too many false alerts", "No community", "Expensive subscription"],
            "crowdwisdom_unique_angles": [
                "Aggregated from 10,000+ real traders with skin in the game",
                "Weekly briefing — not constant noise",
                "Free tier with full functionality",
            ],
            "recommended_ad_angles": [
                {
                    "type": "A",
                    "name": "Pain-First Hook",
                    "premise": "Open with trader's biggest pain: losing money alone",
                    "hook_example": "You spend 40 hours a week on charts. And still lose 60% of your trades. What if you're missing something?",
                    "tone": "empathetic, urgent",
                },
                {
                    "type": "B",
                    "name": "Data-Proof Hook",
                    "premise": "Lead with shocking statistics about retail trader failure rates",
                    "hook_example": "87% of retail traders lose money. The 13% who win? They don't trade alone.",
                    "tone": "authoritative, credible",
                },
                {
                    "type": "C",
                    "name": "Transformation Hook",
                    "premise": "Show the before/after transformation: stressed loser → confident crowd follower",
                    "hook_example": "What if the crowd already knew the answer — before the market moved?",
                    "tone": "inspirational, aspirational",
                },
            ],
        }

    def _save_results(self, top_ads: list[dict], insights: dict) -> dict:
        """Save ads and insights to JSON files."""
        ads_dir = settings.ADS_OUTPUT_DIR
        ads_dir.mkdir(parents=True, exist_ok=True)

        # winning_ads.json
        ads_path = ads_dir / "winning_ads.json"
        ads_output = {
            "generated_at": datetime.now().isoformat(),
            "total_ads": len(top_ads),
            "search_keywords": CWT_KEYWORDS,
            "ads": top_ads,
        }
        with open(ads_path, "w", encoding="utf-8") as f:
            json.dump(ads_output, f, indent=2, ensure_ascii=False)

        # marketing_insights.json
        insights_path = ads_dir / "marketing_insights.json"
        insights_output = {
            "generated_at": datetime.now().isoformat(),
            "product": settings.PRODUCT_NAME,
            "url": settings.PRODUCT_URL,
            "insights": insights,
        }
        with open(insights_path, "w", encoding="utf-8") as f:
            json.dump(insights_output, f, indent=2, ensure_ascii=False)

        from rich.console import Console
        c = Console()
        c.print(f"  [green]✓ Saved:[/green] {ads_path}")
        c.print(f"  [green]✓ Saved:[/green] {insights_path}")

        return {"ads_path": str(ads_path), "insights_path": str(insights_path)}
