from app.agents.base import AgentContext
from app.models.teaching_pack import Assessment, LessonPlan

class AssessmentAgent:
    """Creates an aligned assessment and rubric."""
    async def run(self, context: AgentContext, plan: LessonPlan) -> Assessment:
        # TODO: Call GPT-5.6 with the plan as downstream context.
        raise NotImplementedError

