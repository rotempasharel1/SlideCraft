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

class CoursePage(BaseModel):
    title: str = Field(description="Title of the page")
    content: str = Field(description="Educational content in Markdown format")

class QuizQuestion(BaseModel):
    question: str = Field(description="The multiple choice question")
    options: List[str] = Field(description="List of 4 possible answers")
    correct_answer: str = Field(description="The exact string of the correct option")
    explanation: str = Field(description="Explanation of why this answer is correct")

class CourseGenerationResponse(BaseModel):
    pages: List[CoursePage] = Field(description="3 to 5 pages of structured educational content. Use highly engaging markdown. Be thorough and detailed.")
    quiz: List[QuizQuestion] = Field(description="Exactly 5 multiple-choice questions testing the newly generated content.")
    chat_message: str = Field(description="Message to the user summarizing this chapter, suggesting the exact next topic to learn, and explicitly asking if they want to continue building that next chapter, or if they want to finish and save this course to their library.")

class DraftState(BaseModel):
    messages: list
    course_pages: list
    current_page_index: int
    last_saved_course_id: Optional[str] = None
    course_is_public: Optional[bool] = False