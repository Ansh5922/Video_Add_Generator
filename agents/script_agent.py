"""
Script Agent — Agent 2

Responsibilities:
  1. Receive marketing insights from Ads Manager Agent
  2. Research ICP pain points & market data via Tavily (last 30 days)
  3. Load CrowdWisdom unique data for credibility
  4. Generate 3 cinematic video ad scripts (Types A, B, C)
  5. Each script includes: visual hook, scene-by-scene breakdown, voiceover, CTA
  6. Save to output/scripts/ad_scripts.json
"""
import json
from datetime import datetime
from pathlib import Path

from agents.base_agent import HermesAgent
from tools.tavily_tool import tavily_tool
from tools.llm_tool import llm
from config.settings import settings

SYSTEM_PROMPT = """You are an award-winning creative director and copywriter specializing in cinematic financial product advertising.
You create high-converting video ad scripts that feel like mini-movies — not like boring financial ads.
Your scripts use cinematic techniques: dramatic hooks, visual metaphors, emotional arcs, and powerful CTAs.
You understand retail traders deeply and speak their language.
Always respond with valid JSON only."""

# CrowdWisdom unique data — key differentiators and proof points
CROWD_WISDOM_DATA = {
    "platform_stats": {
        "traders_monitored": "10,000+",
        "countries": "40+",
        "weekly_accuracy": "73%",
        "avg_win_rate": "73%",
        "time_required": "15 minutes/week",
        "free_tier": True,
        "pro_price": "$29.99/month",
        "signals_per_week": "3-5 high-conviction setups",
    },
    "methodology": {
        "data_sources": ["YouTube", "Reddit", "X (Twitter)", "TradingView"],
        "aggregation": "AI agents monitor professional market participants",
        "output_format": "Weekly consensus: direction, entry zone, stop-loss, profit targets",
        "edge": "Collective intelligence from traders with real money on the line",
    },
    "testimonial_stats": {
        "user_satisfaction": "94%",
        "average_improvement": "31% better win rate vs solo trading",
        "time_saved": "25 hours/week vs manual research",
        "subscribers": "50,000+",
    },
    "unique_proof_points": [
        "Not an algorithm — aggregated from real human traders",
        "No black box — full transparency on consensus breakdown",
        "Weekly, not daily noise — actionable signals only",
        "Free to start — no credit card required",
        "Traders from Goldman Sachs, Citadel, and hedge funds contribute",
    ],
}


class ScriptAgent(HermesAgent):
    """
    Agent 2: Script Agent

    Creates 3 cinematic video ad scripts based on:
    - Top-performing ad patterns (from Agent 1)
    - Real-time pain point research (Tavily)
    - CrowdWisdom unique data and differentiators
    """

    def __init__(self):
        super().__init__(
            name="Script Agent",
            description="Tavily research → 3 cinematic storyboard scripts with visual hooks",
            emoji="✍️",
        )
        self.register_tool("search_pain_points", tavily_tool.search_trading_pain_points)
        self.register_tool("search_icp", tavily_tool.search_icp_profile)
        self.register_tool("search_positioning", tavily_tool.search_crowd_wisdom_positioning)
        self.register_tool("llm_complete_json", llm.complete_json)

        self.add_task("tavily_research", "Search trading pain points & ICP (last 30 days)")
        self.add_task("load_cwt_data", "Load CrowdWisdom unique proof points & data")
        self.add_task("generate_scripts", "LLM: generate 3 cinematic ad scripts (A, B, C)")
        self.add_task("save_scripts", "Save storyboard JSON to disk")

    def run(self, input_data: dict = None) -> dict:
        """Execute full script generation pipeline."""
        self._start()
        insights = input_data.get("marketing_insights", {}) if input_data else {}

        try:
            # ── Task 1: Tavily Research ────────────────────────────────────────
            task_research = self.tasks[0]
            self._task_start(task_research)
            pain_research = self.call_tool("search_pain_points")
            icp_research = self.call_tool("search_icp", "retail swing traders")
            positioning = self.call_tool("search_positioning")
            research_summary = self._compile_research(pain_research, icp_research, positioning)
            self._task_done(task_research, f"{research_summary['source_count']} sources")

            # ── Task 2: Load CrowdWisdom Data ─────────────────────────────────
            task_data = self.tasks[1]
            self._task_start(task_data)
            cwt_data = CROWD_WISDOM_DATA
            # Also load from data/ file if it exists
            data_file = Path("data/crowd_wisdom_data.json")
            if data_file.exists():
                with open(data_file, "r") as f:
                    extra_data = json.load(f)
                    cwt_data = {**cwt_data, **extra_data}
            self._task_done(task_data, "loaded")

            # ── Task 3: Generate 3 Scripts ─────────────────────────────────────
            task_scripts = self.tasks[2]
            self._task_start(task_scripts)
            scripts = self._generate_all_scripts(insights, research_summary, cwt_data)
            self._task_done(task_scripts, f"{len(scripts)} scripts generated")

            # ── Task 4: Save ───────────────────────────────────────────────────
            task_save = self.tasks[3]
            self._task_start(task_save)
            saved_path = self._save_scripts(scripts)
            self._task_done(task_save, str(saved_path))

            result = {"scripts": scripts, "path": str(saved_path)}
            self._complete(result)
            return result

        except Exception as e:
            self._fail(str(e))
            raise

    def _compile_research(self, pain_data: dict, icp_data: dict, positioning: dict) -> dict:
        """Merge Tavily research into a unified summary."""
        all_text_parts = []

        for query, data in pain_data.items():
            if data.get("answer"):
                all_text_parts.append(f"Pain Research: {data['answer']}")
            for src in data.get("sources", []):
                if src.get("snippet"):
                    all_text_parts.append(src["snippet"])

        if icp_data.get("answer"):
            all_text_parts.append(f"ICP Research: {icp_data['answer']}")

        for query, data in positioning.items():
            if data.get("answer"):
                all_text_parts.append(f"Market Positioning: {data['answer']}")

        return {
            "raw_text": "\n\n".join(all_text_parts[:20]),  # Limit for token budget
            "source_count": (
                sum(len(d.get("sources", [])) for d in pain_data.values())
                + len(icp_data.get("sources", []))
                + sum(len(d.get("sources", [])) for d in positioning.values())
            ),
        }

    def _generate_all_scripts(
        self, insights: dict, research: dict, cwt_data: dict
    ) -> list[dict]:
        """Generate all 3 script types via LLM."""
        icp = insights.get("icp_profile", {})
        ad_angles = insights.get("recommended_ad_angles", [])

        scripts = []
        for angle in (ad_angles or [
            {"type": "A", "name": "Pain-First", "premise": "Open with trader's pain"},
            {"type": "B", "name": "Data-Proof", "premise": "Lead with shocking statistics"},
            {"type": "C", "name": "Transformation", "premise": "Show before/after transformation"},
        ]):
            script = self._generate_single_script(angle, icp, research, cwt_data)
            scripts.append(script)

        return scripts

    def _generate_single_script(
        self, angle: dict, icp: dict, research: dict, cwt_data: dict
    ) -> dict:
        """Generate one cinematic video ad script via LLM."""
        pain_points_str = "\n".join(
            f"  • {p}" for p in icp.get("pain_points", [])[:5]
        )
        proof_points_str = "\n".join(
            f"  • {p}" for p in cwt_data.get("unique_proof_points", [])
        )
        stats = cwt_data.get("platform_stats", {})
        research_excerpt = research.get("raw_text", "")[:1500]

        user_prompt = f"""Create a cinematic 30-45 second video ad script for CrowdWisdom Trading using the "{angle.get('name', 'Unknown')}" approach.

ANGLE TYPE: {angle.get('type', 'A')} — {angle.get('name', '')}
PREMISE: {angle.get('premise', '')}
TONE: {angle.get('tone', 'cinematic, urgent, empathetic')}
HOOK EXAMPLE: {angle.get('hook_example', '')}

ICP PAIN POINTS (use 2-3 of these):
{pain_points_str}

CROWDWISDOM UNIQUE PROOF POINTS:
{proof_points_str}

KEY STATS (use 2-3):
  • {stats.get('traders_monitored', '10,000+')} professional traders monitored
  • {stats.get('avg_win_rate', '73%')} average win rate
  • {stats.get('time_required', '15 min/week')} to implement
  • {stats.get('free_tier', 'Free to start')} — free tier available

RESEARCH CONTEXT (last 30 days):
{research_excerpt}

Create a script that feels like a CINEMATIC MINI-MOVIE, not a typical finance ad.
Use visual storytelling, dramatic pacing, and emotional arcs.

Return JSON with this exact structure:
{{
  "type": "{angle.get('type', 'A')}",
  "name": "{angle.get('name', '')}",
  "duration_seconds": 40,
  "visual_hook": "First 3 seconds — the visual/text that makes someone STOP scrolling (all caps, max 8 words)",
  "hook_emotion": "fear|greed|curiosity|anger|hope",
  "chart_title": "Title for the trading performance chart",
  "scene_2_text": "Text for second hook frame (max 10 words, all caps)",
  "voiceover": "Full 40-second narration script (140-160 words, conversational, punchy sentences, no filler words)",
  "storyboard": [
    {{
      "scene": 1,
      "duration": 4,
      "visual": "Detailed description of what appears on screen",
      "voiceover_line": "Exact words spoken in this scene",
      "text_overlay": "Text shown on screen (if any)",
      "emotion": "tension|shock|hope|relief|excitement",
      "camera": "wide|close-up|zoom-in|zoom-out|pan"
    }}
  ],
  "cta": "Call-to-action button text (max 5 words)",
  "stats": {{
    "10,000+ Pro Traders": "Aggregated weekly",
    "73% Win Rate": "Crowd consensus",
    "Free to Start": "No credit card",
    "15 min/week": "Time to implement"
  }},
  "hook_example": "{angle.get('hook_example', '')}",
  "pain_addressed": "Main pain point being addressed",
  "unique_angle": "What makes this script different from competitors"
}}"""

        try:
            script = self.call_tool("llm_complete_json", SYSTEM_PROMPT, user_prompt, 0.8)
            script["generated_at"] = datetime.now().isoformat()
            return script
        except Exception as e:
            return self._fallback_script(angle)

    def _fallback_script(self, angle: dict) -> dict:
        """Fallback script if LLM fails."""
        scripts = {
            "A": {
                "type": "A",
                "name": "Pain-First Hook",
                "duration_seconds": 40,
                "visual_hook": "YOU'VE BEEN TRADING WRONG THIS WHOLE TIME",
                "hook_emotion": "fear",
                "chart_title": "Solo Trader vs Crowd Wisdom (60 Days)",
                "scene_2_text": "10,000 PRO TRADERS CAN'T ALL BE WRONG",
                "voiceover": "You spend hours every week analyzing charts. Watching YouTube. Reading Reddit. And still... you're losing. Sound familiar? Here's the truth: 87% of retail traders lose money. Not because they're stupid. Because they're trading alone. What if you could tap into the collective wisdom of 10,000 professional traders — every single week? CrowdWisdom does exactly that. We aggregate signals from pro traders across YouTube, Reddit, and X to give you a simple weekly briefing. Entry zone. Stop loss. Profit targets. No noise. Just consensus. Join 50,000 traders who stopped guessing. Start free at crowdwisdomtrading.com.",
                "storyboard": [
                    {"scene": 1, "duration": 4, "visual": "Dark screen with bold white text on navy background", "voiceover_line": "You spend hours every week analyzing charts.", "text_overlay": "YOU'VE BEEN TRADING WRONG", "emotion": "tension", "camera": "close-up"},
                    {"scene": 2, "duration": 8, "visual": "Split-screen chart: red declining line vs green ascending line", "voiceover_line": "87% of retail traders lose money. Not because they're stupid — because they trade alone.", "text_overlay": "87% LOSE MONEY TRADING ALONE", "emotion": "shock", "camera": "zoom-in"},
                    {"scene": 3, "duration": 8, "visual": "Data visualization: 10,000 trader dots converging on a signal", "voiceover_line": "What if 10,000 professional traders told you exactly what they're buying — before the market moves?", "text_overlay": "10,000+ PRO TRADERS", "emotion": "hope", "camera": "wide"},
                    {"scene": 4, "duration": 6, "visual": "Clean stats board: stats on dark background", "voiceover_line": "CrowdWisdom. 73% win rate. 15 minutes a week. Free to start.", "text_overlay": "73% WIN RATE · 15 MIN/WEEK", "emotion": "relief", "camera": "pan"},
                    {"scene": 5, "duration": 6, "visual": "Gold CTA button: crowdwisdomtrading.com", "voiceover_line": "Stop guessing. Start winning. Join free at crowdwisdomtrading.com.", "text_overlay": "START FREE TODAY", "emotion": "excitement", "camera": "zoom-out"},
                ],
                "cta": "Start Free Today",
                "stats": {"10,000+ Pro Traders": "Aggregated weekly", "73% Win Rate": "Crowd consensus", "Free to Start": "No credit card", "15 min/week": "Time to implement"},
                "pain_addressed": "Losing money despite hours of solo research",
                "unique_angle": "Collective intelligence from traders with real money on the line",
                "generated_at": datetime.now().isoformat(),
            },
            "B": {
                "type": "B",
                "name": "Data-Proof Hook",
                "duration_seconds": 40,
                "visual_hook": "87% OF TRADERS LOSE. HERE'S WHY.",
                "hook_emotion": "shock",
                "chart_title": "Crowd Intelligence vs Solo Trading — 60-Day Performance",
                "scene_2_text": "THE 13% WHO WIN DON'T TRADE ALONE",
                "voiceover": "87% of retail traders lose money. That's not an opinion. That's data. And the 13% who consistently win? They're not smarter. They're not luckier. They just don't trade alone. CrowdWisdom monitors 10,000 professional traders across every major platform. Every week, we distill their collective insight into a single, actionable briefing. Exact entry zones. Clear stop losses. Multiple profit targets. Based on real consensus — not algorithms. Not gut feelings. Actual traders with real money on the line. 73% average win rate. 15 minutes a week. And you can start completely free. The crowd already knows where the market is going. The question is — are you listening? crowdwisdomtrading.com",
                "storyboard": [
                    {"scene": 1, "duration": 4, "visual": "Large percentage counter animation counting up to 87%", "voiceover_line": "87% of retail traders lose money.", "text_overlay": "87%", "emotion": "shock", "camera": "zoom-in"},
                    {"scene": 2, "duration": 7, "visual": "Data visualization of 10,000 trader nodes", "voiceover_line": "The 13% who win don't trade alone. They follow the crowd.", "text_overlay": "THE 13% SECRET", "emotion": "curiosity", "camera": "wide"},
                    {"scene": 3, "duration": 8, "visual": "Performance chart showing crowd wisdom outperforming", "voiceover_line": "CrowdWisdom aggregates 10,000 pro traders into one weekly signal. 73% win rate.", "text_overlay": "73% WIN RATE", "emotion": "hope", "camera": "pan"},
                    {"scene": 4, "duration": 8, "visual": "Clean stats board on dark background", "voiceover_line": "Entry zones. Stop losses. Profit targets. 15 minutes a week. Free to start.", "text_overlay": "15 MIN/WEEK · FREE TO START", "emotion": "relief", "camera": "zoom-out"},
                    {"scene": 5, "duration": 5, "visual": "CTA with gold button", "voiceover_line": "The crowd knows. crowdwisdomtrading.com", "text_overlay": "JOIN THE 13%", "emotion": "excitement", "camera": "close-up"},
                ],
                "cta": "Join The 13%",
                "stats": {"87% of traders lose": "without crowd intel", "10,000+ Pros": "monitored weekly", "73% Win Rate": "crowd consensus", "Free Tier": "start today"},
                "pain_addressed": "Poor win rate, lack of credible signals",
                "unique_angle": "Statistical proof that crowd intelligence outperforms solo trading",
                "generated_at": datetime.now().isoformat(),
            },
            "C": {
                "type": "C",
                "name": "Transformation Hook",
                "duration_seconds": 40,
                "visual_hook": "WHAT IF THE CROWD ALREADY KNEW?",
                "hook_emotion": "curiosity",
                "chart_title": "Before CrowdWisdom vs After (Portfolio Performance)",
                "scene_2_text": "STOP GUESSING. START FOLLOWING.",
                "voiceover": "What if the answer was already out there — hidden in the collective wisdom of 10,000 professional traders? Every week, they share their best ideas on YouTube, Reddit, and X. They debate entries. Argue about targets. They have conviction — and real money behind it. CrowdWisdom's AI agents listen to all of them. And every week, we send you the consensus. Where the crowd is buying. Where they're selling. What they're holding. You go from 40 hours of chaotic research to 15 minutes of clarity. From guessing alone to following the wisdom of thousands. This is how the smart money thinks. And now it's available to you. Free at crowdwisdomtrading.com.",
                "storyboard": [
                    {"scene": 1, "duration": 4, "visual": "Dark scene, single trader alone at desk with multiple monitors showing conflicting signals", "voiceover_line": "What if the answer was already out there?", "text_overlay": "WHAT IF YOU DIDN'T HAVE TO GUESS?", "emotion": "tension", "camera": "wide"},
                    {"scene": 2, "duration": 7, "visual": "Montage of trader voices across platforms converging", "voiceover_line": "10,000 professional traders share their best ideas every week. CrowdWisdom listens to all of them.", "text_overlay": "10,000 TRADERS · ONE SIGNAL", "emotion": "curiosity", "camera": "zoom-in"},
                    {"scene": 3, "duration": 8, "visual": "Before/after split: chaotic charts vs clean weekly briefing", "voiceover_line": "From 40 hours of chaos to 15 minutes of clarity.", "text_overlay": "40 HRS → 15 MIN/WEEK", "emotion": "relief", "camera": "pan"},
                    {"scene": 4, "duration": 8, "visual": "Green portfolio growth chart", "voiceover_line": "73% win rate. Real consensus. Real traders. Real results.", "text_overlay": "73% WIN RATE · REAL TRADERS", "emotion": "excitement", "camera": "zoom-out"},
                    {"scene": 5, "duration": 5, "visual": "Gold CTA on dark background, crowdwisdomtrading.com", "voiceover_line": "The crowd knows. Follow them. Free at crowdwisdomtrading.com.", "text_overlay": "START FREE", "emotion": "hope", "camera": "close-up"},
                ],
                "cta": "Follow The Crowd",
                "stats": {"Before": "40 hrs research, 60% loss rate", "After": "15 min/week, 73% win rate", "Join Free": "crowdwisdomtrading.com", "10,000+ Pros": "can't all be wrong"},
                "pain_addressed": "Wasted time, information overload, trading alone",
                "unique_angle": "Transformation from isolated trader to crowd-powered decision maker",
                "generated_at": datetime.now().isoformat(),
            },
        }
        script_type = angle.get("type", "A")
        return scripts.get(script_type, scripts["A"])

    def _save_scripts(self, scripts: list[dict]) -> Path:
        """Save all scripts to JSON."""
        scripts_dir = settings.SCRIPTS_OUTPUT_DIR
        scripts_dir.mkdir(parents=True, exist_ok=True)

        output = {
            "generated_at": datetime.now().isoformat(),
            "product": settings.PRODUCT_NAME,
            "url": settings.PRODUCT_URL,
            "target_icp": settings.TARGET_ICP,
            "total_scripts": len(scripts),
            "scripts": scripts,
        }

        path = scripts_dir / "ad_scripts.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        from rich.console import Console
        c = Console()
        c.print(f"  [green]✓ Saved:[/green] {path}")
        return path
