from pydantic import BaseModel, Field

class LessonRequest(BaseModel):
    description: str = Field(min_length=10, max_length=4000, description="Descripción libre de la clase.")

