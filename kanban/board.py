"""
Hermes Kanban Board — Real-time visual pipeline tracker.

Renders a Rich terminal Kanban board showing:
  BACKLOG | IN PROGRESS | DONE | FAILED
for all agents and their tasks.
"""
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from agents.base_agent import AgentStatus, HermesAgent

console = Console()

# Status → color + icon mapping
STATUS_STYLE = {
    AgentStatus.BACKLOG:     ("[dim]", "○", "dim"),
    AgentStatus.IN_PROGRESS: ("[bold yellow]", "◎", "bold yellow"),
    AgentStatus.DONE:        ("[bold green]", "●", "bold green"),
    AgentStatus.FAILED:      ("[bold red]", "✕", "bold red"),
    AgentStatus.SKIPPED:     ("[dim]", "—", "dim"),
}


def _agent_panel(agent: HermesAgent, width: int = 38) -> Panel:
    """Render a single agent as a Kanban card."""
    _, icon, style = STATUS_STYLE.get(agent.status, ("", "?", "white"))
    title = f"{agent.emoji} {agent.name}"

    table = Table(box=None, show_header=False, padding=(0, 1), expand=True)
    table.add_column("icon", width=3, no_wrap=True)
    table.add_column("task", style="dim")
    table.add_column("dur", justify="right", width=7, style="dim cyan")

    for task in agent.tasks:
        t_icon, _, t_style = STATUS_STYLE.get(task.status, ("", "?", "white"))[::-1]
        _, t_icon, t_style = STATUS_STYLE.get(task.status, ("", "○", "dim"))
        dur = f"{task.duration:.0f}s" if task.duration > 0 else ""
        name_text = Text(task.name.replace("_", " ").title(), style=t_style)
        table.add_row(
            Text(t_icon, style=t_style),
            name_text,
            Text(dur, style="dim cyan"),
        )

    # Agent duration
    dur_str = ""
    if agent.duration > 0:
        dur_str = f" ({agent.duration:.0f}s)"

    border_style = {
        AgentStatus.BACKLOG:     "dim",
        AgentStatus.IN_PROGRESS: "yellow",
        AgentStatus.DONE:        "green",
        AgentStatus.FAILED:      "red",
        AgentStatus.SKIPPED:     "dim",
    }.get(agent.status, "white")

    return Panel(
        table,
        title=f"[{border_style}]{icon} {title}{dur_str}[/]",
        border_style=border_style,
        expand=True,
    )


def render_kanban(agents: list[HermesAgent], elapsed: float = 0) -> Table:
    """Render the full Hermes Kanban board as a Rich Table."""
    # Group agents by status column
    backlog = [a for a in agents if a.status == AgentStatus.BACKLOG]
    in_progress = [a for a in agents if a.status == AgentStatus.IN_PROGRESS]
    done = [a for a in agents if a.status in (AgentStatus.DONE, AgentStatus.FAILED, AgentStatus.SKIPPED)]

    board = Table(
        box=box.DOUBLE_EDGE,
        expand=True,
        title=f"[bold cyan]⚡ HERMES KANBAN — CrowdWisdom Video Ad Pipeline[/bold cyan]",
        caption=f"[dim]elapsed: {elapsed:.0f}s[/dim]",
        show_header=True,
        header_style="bold",
        border_style="cyan",
    )
    board.add_column("○  BACKLOG", style="dim", ratio=1)
    board.add_column("◎  IN PROGRESS", style="yellow", ratio=1)
    board.add_column("●  DONE / FAILED", style="green", ratio=1)

    max_rows = max(len(backlog), len(in_progress), len(done), 1)

    for i in range(max_rows):
        b_cell = _agent_panel(backlog[i]) if i < len(backlog) else ""
        p_cell = _agent_panel(in_progress[i]) if i < len(in_progress) else ""
        d_cell = _agent_panel(done[i]) if i < len(done) else ""
        board.add_row(b_cell, p_cell, d_cell)

    return board


class KanbanBoard:
    """
    Live-updating Hermes Kanban board.

    Usage:
        board = KanbanBoard(agents)
        board.start()
        # ... run agents ...
        board.update()  # refresh display
        board.stop()
    """

    def __init__(self, agents: list[HermesAgent]):
        self.agents = agents
        self._start_time = datetime.now()
        self._live: Optional[Live] = None

    def _elapsed(self) -> float:
        return (datetime.now() - self._start_time).total_seconds()

    def render(self) -> Table:
        return render_kanban(self.agents, self._elapsed())

    def start(self):
        """Start the live Kanban display."""
        self._live = Live(self.render(), console=console, refresh_per_second=2)
        self._live.start()

    def update(self):
        """Refresh the Kanban board."""
        if self._live:
            self._live.update(self.render())

    def stop(self):
        """Stop the live display."""
        if self._live:
            self._live.stop()
        # Print final board
        console.print(self.render())

    def print_summary(self, total_elapsed: float):
        """Print pipeline completion summary."""
        done = sum(1 for a in self.agents if a.status == AgentStatus.DONE)
        failed = sum(1 for a in self.agents if a.status == AgentStatus.FAILED)

        console.print()
        console.print(
            Panel(
                f"[bold green]Pipeline Complete![/bold green]\n\n"
                f"  Agents Done:    [green]{done}/{len(self.agents)}[/green]\n"
                f"  Agents Failed:  [{'red' if failed else 'green'}]{failed}[/]\n"
                f"  Total Time:     [cyan]{total_elapsed:.1f}s[/cyan]\n\n"
                f"  [bold]Outputs:[/bold]\n"
                f"  📊  output/ads/winning_ads.json\n"
                f"  📊  output/ads/marketing_insights.json\n"
                f"  ✍️   output/scripts/ad_scripts.json\n"
                f"  🎬  output/videos/crowdwisdom_ad_v1.mp4\n"
                f"  🎬  output/videos/crowdwisdom_ad_v2.mp4\n"
                f"  🎬  output/videos/crowdwisdom_ad_v3.mp4",
                title="[bold cyan]⚡ Hermes Pipeline Complete[/bold cyan]",
                border_style="green" if not failed else "yellow",
            )
        )
