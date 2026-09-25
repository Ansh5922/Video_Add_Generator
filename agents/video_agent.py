"""
Video Agent — Agent 3

Responsibilities:
  1. Receive 3 scripts from Script Agent
  2. Generate cinematic video frames (PIL: dark, financial aesthetic)
  3. Render trading charts with matplotlib
  4. Generate narration audio (gTTS)
  5. Compose final videos with FFmpeg (Ken Burns, color grading, audio mix)
  6. Output 3 MP4 files: crowdwisdom_ad_v1.mp4, _v2.mp4, _v3.mp4
"""
from pathlib import Path
from datetime import datetime

from agents.base_agent import HermesAgent
from tools.video_tool import video_tool
from config.settings import settings


class VideoAgent(HermesAgent):
    """
    Agent 3: Video Agent

    Takes the 3 scripts from the Script Agent and renders them into
    cinematic 30-45 second video ads using:
    - PIL for dark, cinematic frame generation
    - matplotlib for trading performance charts
    - gTTS for voiceover narration
    - FFmpeg for video composition, Ken Burns effect, and color grading
    """

    def __init__(self):
        super().__init__(
            name="Video Agent",
            description="Frame generation → audio → FFmpeg composition → cinematic color grade",
            emoji="🎬",
        )
        self.register_tool("generate_video", video_tool.generate_video)

        self.add_task("setup_pipeline", "Initialize video pipeline & directories")
        self.add_task("render_v1", "Render Type A: Pain-First Hook (30-45s)")
        self.add_task("render_v2", "Render Type B: Data-Proof Hook (30-45s)")
        self.add_task("render_v3", "Render Type C: Transformation Hook (30-45s)")
        self.add_task("verify_output", "Verify MP4 files & report durations")

    def run(self, input_data: dict = None) -> dict:
        """Execute full video rendering pipeline."""
        self._start()
        scripts = []

        if input_data:
            scripts = input_data.get("scripts", [])

        if not scripts:
            from rich.console import Console
            Console().print(
                "  [yellow]⚠ No scripts provided, using fallback scripts[/yellow]"
            )
            scripts = self._get_fallback_scripts()

        try:
            # ── Task 1: Setup ──────────────────────────────────────────────────
            task_setup = self.tasks[0]
            self._task_start(task_setup)
            settings.ensure_dirs()
            self._task_done(task_setup, "ready")

            # ── Tasks 2-4: Render each video ───────────────────────────────────
            render_tasks = [self.tasks[1], self.tasks[2], self.tasks[3]]
            versions = ["v1", "v2", "v3"]
            output_paths = []

            for script, task, version in zip(scripts[:3], render_tasks, versions):
                self._task_start(task)
                try:
                    path = self.call_tool("generate_video", script, version)
                    if path:
                        output_paths.append(path)
                        self._task_done(task, str(path))
                    else:
                        self._task_fail(task, "FFmpeg composition returned None")
                except Exception as e:
                    self._task_fail(task, str(e))

            # Fill remaining versions if fewer scripts provided
            for i in range(len(scripts), 3):
                render_tasks[i].status = self.tasks[i + 1].status if i + 1 < len(self.tasks) else render_tasks[i].status
                self.tasks[i + 1].status = __import__("agents.base_agent", fromlist=["AgentStatus"]).AgentStatus.SKIPPED

            # ── Task 5: Verify ─────────────────────────────────────────────────
            task_verify = self.tasks[4]
            self._task_start(task_verify)
            report = self._verify_outputs(output_paths)
            self._task_done(task_verify, f"{len(output_paths)} videos OK")

            result = {
                "videos": [str(p) for p in output_paths],
                "report": report,
            }
            self._complete(result)
            return result

        except Exception as e:
            self._fail(str(e))
            raise

    def _verify_outputs(self, paths: list[Path]) -> dict:
        """Check MP4 files exist and report file sizes."""
        from rich.console import Console
        c = Console()
        report = {"videos": []}

        for path in paths:
            if path and Path(path).exists():
                size_mb = Path(path).stat().st_size / (1024 * 1024)
                report["videos"].append({
                    "path": str(path),
                    "size_mb": round(size_mb, 2),
                    "exists": True,
                })
                c.print(f"  [green]✓[/green] {Path(path).name} ({size_mb:.1f} MB)")
            else:
                report["videos"].append({"path": str(path), "exists": False})
                c.print(f"  [red]✗[/red] {path} — not found")

        return report

    def _get_fallback_scripts(self) -> list[dict]:
        """Minimal fallback scripts if no input provided."""
        return [
            {
                "type": "A",
                "visual_hook": "YOU'VE BEEN TRADING WRONG THIS WHOLE TIME",
                "hook_emotion": "fear",
                "chart_title": "Solo Trader vs Crowd Wisdom (60 Days)",
                "scene_2_text": "10,000 PRO TRADERS CAN'T ALL BE WRONG",
                "voiceover": "87% of retail traders lose money. Not because they're stupid. Because they trade alone. CrowdWisdom aggregates signals from 10,000 professional traders every week. 73% win rate. 15 minutes a week. Free to start. Stop guessing. Start winning. crowdwisdomtrading.com",
                "cta": "Start Free Today",
                "stats": {"10,000+ Pro Traders": "Weekly signals", "73% Win Rate": "Crowd consensus", "Free to Start": "No credit card", "15 min/week": "All it takes"},
            },
            {
                "type": "B",
                "visual_hook": "87% OF TRADERS LOSE. HERE'S WHY.",
                "hook_emotion": "shock",
                "chart_title": "Crowd Intelligence vs Solo Trading — 60-Day Performance",
                "scene_2_text": "THE 13% WHO WIN DON'T TRADE ALONE",
                "voiceover": "87% of retail traders lose money. The 13% who consistently win don't trade alone. CrowdWisdom monitors 10,000 professional traders and delivers one clear weekly signal. Entry zones. Stop losses. Profit targets. 73% average win rate. Start free at crowdwisdomtrading.com.",
                "cta": "Join The 13%",
                "stats": {"87% Lose": "Trading alone", "13% Win": "With crowd intel", "10,000+ Pros": "Monitored weekly", "Free Tier": "Available now"},
            },
            {
                "type": "C",
                "visual_hook": "WHAT IF THE CROWD ALREADY KNEW?",
                "hook_emotion": "curiosity",
                "chart_title": "Before & After CrowdWisdom (Portfolio Performance)",
                "scene_2_text": "FROM 40 HOURS TO 15 MINUTES A WEEK",
                "voiceover": "What if the answer was already there — in the collective wisdom of 10,000 professional traders? CrowdWisdom listens to all of them. And every week, we send you the consensus. From 40 hours of chaos to 15 minutes of clarity. 73% win rate. Free to start. crowdwisdomtrading.com.",
                "cta": "Follow The Crowd",
                "stats": {"Before": "40 hrs, 60% loss", "After": "15 min, 73% wins", "Join Free": "Start today", "10,000+": "Pro traders"},
            },
        ]
