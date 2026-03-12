from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProjectCreate(BaseModel):
    title: str
    content: str
    is_public: bool = False


class Project(BaseModel):
    id: str
    owner_id: str
    title: str
    content: str
    is_public: bool
    created_at: datetime


class ChatRequest(BaseModel):
    prompt: str
    context: Optional[str] = None

class EmailLoginRequest(BaseModel):
    email: str

class Slide(BaseModel):
    title: str = Field(description="Title of the slide")
    content: str = Field(description="Content of the slide in Markdown format. Use bullet points and concise text.")
    design_hint: str = Field(description="Brief hint on how to visually design this slide (e.g., 'Use a large image on the left', 'Comparison table').")

class LessonPlan(BaseModel):
    objective: str = Field(description="The main educational objective of this lesson.")
    duration: str = Field(description="Recommended duration (e.g., '45 minutes').")
    activities: List[str] = Field(description="List of step-by-step activities for the teacher.")
    materials_needed: List[str] = Field(description="List of materials or resources needed.")

class QuizQuestion(BaseModel):
    question: str = Field(description="The multiple choice question")
    options: List[str] = Field(description="List of 4 possible answers")
    correct_answer: str = Field(description="The exact string of the correct option")
    explanation: str = Field(description="Explanation of why this answer is correct")

class CourseGenerationResponse(BaseModel):
    slides: List[Slide] = Field(description="5 to 7 slides for the presentation. Focus on high-impact visual content.")
    lesson_plan: LessonPlan = Field(description="A detailed lesson plan corresponding to the presentation.")
    quiz: List[QuizQuestion] = Field(description="Exactly 5 multiple-choice questions testing the newly generated content.")
    chat_message: str = Field(description="Message to the user summarizing the lesson, and asking if they want to save it or build another topic.")

class RedesignResponse(BaseModel):
    slides: List[Slide] = Field(description="The redesigned version of the input slides, with better structure and design hints.")
    chat_message: str = Field(description="Summary of the changes and design improvements made.")

class DraftState(BaseModel):
    messages: list
    course_pages: list
    current_page_index: int
    last_saved_course_id: Optional[str] = None
    course_is_public: Optional[bool] = False