from app.agents.base import Agent, AgentContext
from app.models.teaching_pack import LessonPlan

class PlannerAgent(Agent[LessonPlan]):
    """Maps a request to curriculum objectives and lesson structure."""
    async def run(self, context: AgentContext) -> LessonPlan:
        # TODO: Call GPT-5.6 with shared context first and return structured output.
        raise NotImplementedError

