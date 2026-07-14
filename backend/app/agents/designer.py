from app.agents.base import AgentContext
from app.models.teaching_pack import ActivityGuide, LessonPlan

class DesignerAgent:
    """Creates activities from an approved lesson plan."""
    async def run(self, context: AgentContext, plan: LessonPlan) -> ActivityGuide:
        # TODO: Call GPT-5.6 with the plan as downstream context.
        raise NotImplementedError

