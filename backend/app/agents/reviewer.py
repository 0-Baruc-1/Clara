from app.agents.base import AgentContext
from app.models.teaching_pack import ActivityGuide, Assessment, LessonPlan

class ReviewerAgent:
    """Checks consistency across the three artifacts."""
    async def run(self, context: AgentContext, plan: LessonPlan, activities: ActivityGuide, assessment: Assessment) -> list[str]:
        # TODO: Call GPT-5.6 to identify or resolve cross-artifact inconsistencies.
        raise NotImplementedError

