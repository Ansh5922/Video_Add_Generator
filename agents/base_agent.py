"""
Base Agent — Hermes-style agent base class.

Provides:
- Tool registration and invocation
- Status tracking (Backlog → In Progress → Done / Failed)
- Result storage
- Structured logging
"""
import time
from enum import Enum
from typing import Any, Callable, Optional
from rich.console import Console
from rich.panel import Panel

console = Console()


class AgentStatus(str, Enum):
    BACKLOG = "BACKLOG"
    IN_PROGRESS = "IN PROGRESS"
    DONE = "DONE"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class AgentTask:
    """A single atomic task within an agent."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status: AgentStatus = AgentStatus.BACKLOG
        self.result: Any = None
        self.error: Optional[str] = None
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None

    @property
    def duration(self) -> float:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return 0.0


class HermesAgent:
    """
    Hermes-style agent base class.

    Each agent has:
    - A name and description (shown in Kanban)
    - A list of tasks it will execute
    - Registered tools it can call
    - Input/output data passed between agents
    """

    def __init__(self, name: str, description: str, emoji: str = "🤖"):
        self.name = name
        self.description = description
        self.emoji = emoji
        self.status: AgentStatus = AgentStatus.BACKLOG
        self.tasks: list[AgentTask] = []
        self.tools: dict[str, Callable] = {}
        self.result: Any = None
        self.error: Optional[str] = None
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self._input_data: Any = None

    def register_tool(self, name: str, func: Callable):
        """Register a tool this agent can call."""
        self.tools[name] = func

    def add_task(self, name: str, description: str) -> AgentTask:
        """Add a task to this agent's queue."""
        task = AgentTask(name, description)
        self.tasks.append(task)
        return task

    def call_tool(self, name: str, *args, **kwargs) -> Any:
        """Invoke a registered tool by name."""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not registered on agent '{self.name}'")
        return self.tools[name](*args, **kwargs)

    def set_input(self, data: Any):
        """Set input data from a previous agent."""
        self._input_data = data

    @property
    def duration(self) -> float:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return 0.0

    def _start(self):
        self.status = AgentStatus.IN_PROGRESS
        self.started_at = time.time()
        console.print(
            Panel(
                f"[bold]{self.emoji} {self.name}[/bold]\n[dim]{self.description}[/dim]",
                border_style="cyan",
                expand=False,
            )
        )

    def _complete(self, result: Any):
        self.result = result
        self.status = AgentStatus.DONE
        self.completed_at = time.time()
        console.print(
            f"  [bold green]✅ {self.name} completed[/bold green] "
            f"[dim]({self.duration:.1f}s)[/dim]"
        )

    def _fail(self, error: str):
        self.error = error
        self.status = AgentStatus.FAILED
        self.completed_at = time.time()
        console.print(f"  [bold red]❌ {self.name} failed:[/bold red] {error}")

    def _task_start(self, task: AgentTask):
        task.status = AgentStatus.IN_PROGRESS
        task.started_at = time.time()
        console.print(f"  [bold]  ▶ {task.name}[/bold] — {task.description}")

    def _task_done(self, task: AgentTask, result: Any = None):
        task.status = AgentStatus.DONE
        task.result = result
        task.completed_at = time.time()
        console.print(
            f"  [green]  ✓ {task.name}[/green] [dim]({task.duration:.1f}s)[/dim]"
        )

    def _task_fail(self, task: AgentTask, error: str):
        task.status = AgentStatus.FAILED
        task.error = error
        task.completed_at = time.time()
        console.print(f"  [red]  ✗ {task.name}:[/red] {error}")

    def run(self, input_data: Any = None) -> Any:
        """Override in subclasses to implement agent logic."""
        raise NotImplementedError("Subclasses must implement run()")
