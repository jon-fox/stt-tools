from pydantic import BaseModel
from openai import OpenAI
from src.config.constants import OPEN_AI_MODEL_TYPE
# client = OpenAI()

# https://platform.openai.com/docs/guides/structured-outputs/supported-schemas?context=ex2

class ResearchPaperExtraction(BaseModel):
    title: str
    authors: list[str]
    abstract: str
    keywords: list[str]

completion = client.beta.chat.completions.parse(
    model=OPEN_AI_MODEL_TYPE,
    messages=[
        {"role": "system", "content": ""},
        {"role": "user", "content": ""}
    ],
    response_format=ResearchPaperExtraction,
)

research_paper = completion.choices[0].message.parsed