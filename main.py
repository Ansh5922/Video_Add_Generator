# -*- coding: utf-8 -*-
"""
CrowdWisdom Video Ad Agent -- Hermes Pipeline Orchestrator
==========================================================

Entry point for the complete 3-agent Hermes pipeline:

  Agent 1: Ads Manager Agent  ->  Scrape Meta Ads + extract insights
  Agent 2: Script Agent       ->  Research + generate 3 cinematic scripts
  Agent 3: Video Agent        ->  Render 3 MP4 video ads

Run: python main.py [--agent ads|script|video] [--use-cache] [--verbose]
"""
import sys
import io
import time
import json
import os
import click
from pathlib import Path
from datetime import datetime

# Force UTF-8 output on Windows to support Rich characters
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

# ── Project imports ────────────────────────────────────────────────────────────
from config.settings import settings
from agents.ads_manager_agent import AdsManagerAgent
from agents.script_agent import ScriptAgent
from agents.video_agent import VideoAgent
from kanban.board import KanbanBoard

console = Console()

BANNER = """  CROWDWISDOM VIDEO AD AGENT  |  Hermes Multi-Agent Pipeline  """


def print_banner():
    """Print the startup banner."""
    console.print(f"[bold cyan on dark_blue] {BANNER} [/bold cyan on dark_blue]")
    console.print(
        Panel(
            "[bold]🎬 CrowdWisdom Video Ad Agent[/bold] — Hermes Multi-Agent Pipeline\n\n"
            "  📊 [cyan]Agent 1:[/cyan] Ads Manager  — Meta Ads scraper via Apify\n"
            "  ✍️   [cyan]Agent 2:[/cyan] Script Agent — 3 cinematic scripts via Tavily + LLM\n"
            "  🎬 [cyan]Agent 3:[/cyan] Video Agent  — Cinematic MP4 via PIL + FFmpeg\n\n"
            f"  Product: [bold]{settings.PRODUCT_NAME}[/bold] — {settings.PRODUCT_URL}\n"
            f"  LLM:     [bold]{settings.OPENROUTER_MODEL}[/bold] via OpenRouter",
            border_style="cyan",
        )
    )


def load_cached_ads() -> dict:
    """Load previously scraped ads from disk."""
    ads_path = settings.ADS_OUTPUT_DIR / "winning_ads.json"
    insights_path = settings.ADS_OUTPUT_DIR / "marketing_insights.json"

    if ads_path.exists() and insights_path.exists():
        with open(ads_path) as f:
            ads_data = json.load(f)
        with open(insights_path) as f:
            insights_data = json.load(f)
        console.print(f"  [green]✓ Loaded cached ads:[/green] {ads_path}")
        return {
            "top_ads": ads_data.get("ads", []),
            "marketing_insights": insights_data.get("insights", {}),
        }
    return {}


def load_cached_scripts() -> dict:
    """Load previously generated scripts from disk."""
    scripts_path = settings.SCRIPTS_OUTPUT_DIR / "ad_scripts.json"
    if scripts_path.exists():
        with open(scripts_path) as f:
            data = json.load(f)
        console.print(f"  [green]✓ Loaded cached scripts:[/green] {scripts_path}")
        return {"scripts": data.get("scripts", [])}
    return {}


def run_full_pipeline(use_cache: bool = False, verbose: bool = False) -> dict:
    """
    Execute the complete 3-agent Hermes pipeline.

    Pipeline:
      AdsManagerAgent → ScriptAgent → VideoAgent

    Args:
        use_cache: Skip scraping/search if cached results exist
        verbose: Show detailed tool outputs

    Returns:
        Final pipeline result dict
    """
    # Validate config
    try:
        settings.validate()
    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        sys.exit(1)

    settings.ensure_dirs()

    # Initialize agents
    ads_agent = AdsManagerAgent()
    script_agent = ScriptAgent()
    video_agent = VideoAgent()
    agents = [ads_agent, script_agent, video_agent]

    # Start Kanban board
    kanban = KanbanBoard(agents)
    start_time = time.time()

    print_banner()
    console.print(Rule("[cyan]Starting Hermes Pipeline[/cyan]"))
    console.print()

    # ── Agent 1: Ads Manager ───────────────────────────────────────────────────
    console.print(Rule("[yellow]Agent 1: Ads Manager[/yellow]"))
    if use_cache:
        cached_ads = load_cached_ads()
        if cached_ads:
            ads_agent.status = __import__("agents.base_agent", fromlist=["AgentStatus"]).AgentStatus.DONE
            ads_agent.result = cached_ads
            ads_result = cached_ads
            console.print("  [dim]Skipped scraping (--use-cache)[/dim]")
        else:
            ads_result = ads_agent.run()
    else:
        ads_result = ads_agent.run()

    console.print()

    # ── Agent 2: Script Agent ──────────────────────────────────────────────────
    console.print(Rule("[yellow]Agent 2: Script Agent[/yellow]"))
    if use_cache:
        cached_scripts = load_cached_scripts()
        if cached_scripts:
            script_agent.status = __import__("agents.base_agent", fromlist=["AgentStatus"]).AgentStatus.DONE
            script_agent.result = cached_scripts
            script_result = cached_scripts
            console.print("  [dim]Skipped search (--use-cache)[/dim]")
        else:
            script_result = script_agent.run(ads_result)
    else:
        script_result = script_agent.run(ads_result)

    console.print()

    # ── Agent 3: Video Agent ───────────────────────────────────────────────────
    console.print(Rule("[yellow]Agent 3: Video Agent[/yellow]"))
    video_result = video_agent.run(script_result)
    console.print()

    # ── Final Summary ──────────────────────────────────────────────────────────
    total_elapsed = time.time() - start_time
    console.print(Rule("[green]Pipeline Complete[/green]"))
    kanban.print_summary(total_elapsed)

    return {
        "ads": ads_result,
        "scripts": script_result,
        "videos": video_result,
        "elapsed_seconds": total_elapsed,
    }


def run_single_agent(agent_name: str) -> dict:
    """Run a single agent with available cached data."""
    try:
        settings.validate()
    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        sys.exit(1)

    settings.ensure_dirs()

    if agent_name == "ads":
        agent = AdsManagerAgent()
        kanban = KanbanBoard([agent])
        print_banner()
        result = agent.run()
        kanban.print_summary(agent.duration)
        return result

    elif agent_name == "script":
        agent = ScriptAgent()
        kanban = KanbanBoard([agent])
        print_banner()
        ads_data = load_cached_ads()
        result = agent.run(ads_data)
        kanban.print_summary(agent.duration)
        return result

    elif agent_name == "video":
        agent = VideoAgent()
        kanban = KanbanBoard([agent])
        print_banner()
        scripts_data = load_cached_scripts()
        result = agent.run(scripts_data)
        kanban.print_summary(agent.duration)
        return result

    else:
        console.print(f"[red]Unknown agent:[/red] {agent_name}. Choose: ads, script, video")
        sys.exit(1)


# ─── CLI ───────────────────────────────────────────────────────────────────────


@click.command()
@click.option(
    "--agent",
    type=click.Choice(["ads", "script", "video", "all"]),
    default="all",
    help="Which agent to run (default: all)",
)
@click.option(
    "--use-cache",
    is_flag=True,
    default=False,
    help="Use cached ads/scripts instead of re-scraping",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output",
)
def main(agent: str, use_cache: bool, verbose: bool):
    """
    🎬 CrowdWisdom Video Ad Agent — Hermes Multi-Agent Pipeline

    Generates cinematic video ads for crowdwisdomtrading.com using
    3 AI agents: Ads Manager, Script, and Video.
    """
    if agent == "all":
        run_full_pipeline(use_cache=use_cache, verbose=verbose)
    else:
        run_single_agent(agent)


if __name__ == "__main__":
    main()
