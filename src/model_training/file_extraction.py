from pydantic import BaseModel
from openai import OpenAI
from src.config.constants import OPEN_AI_MODEL_TYPE
# client = OpenAI()

# https://platform.openai.com/docs/guides/structured-outputs/supported-schemas?context=ex2

class ResponseExtraction(BaseModel):
    Confidence_Score: int
    Timestamps: str


completion = client.beta.chat.completions.parse(
    model=OPEN_AI_MODEL_TYPE,
    messages=[
        {"role": "system", "content": ""},
        {"role": "user", "content": ""}
    ],
    response_format=ResponseExtraction,
)

response = completion.choices[0].message.parsed