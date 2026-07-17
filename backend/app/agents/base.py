from dataclasses import dataclass
from typing import Protocol, TypeVar
from app.models.requests import LessonRequest

OutputT = TypeVar("OutputT")

@dataclass(frozen=True)
class AgentContext:
    """Shared immutable context passed to every agent."""
    request: LessonRequest
    system_context: str
    model: str
    # Request-scoped only: never persisted, serialized, or included in SSE data.
    api_key: str | None = None

class Agent(Protocol[OutputT]):
    async def run(self, context: AgentContext) -> OutputT: ...
