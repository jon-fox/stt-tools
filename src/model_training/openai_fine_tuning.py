import json
import openai
import os
# import pandas as pd
from pprint import pprint
from src.config.constants import *
import glob

client = openai.OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    organization=os.environ.get("OPENAI_ORG_ID"),
    project=os.environ.get("OPENAI_PROJECT_ID"),
)

def get_file_path(pattern):
    # Construct the path two directories up
    base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
    
    # Define the full pattern to match the file name
    full_pattern = os.path.join(base_dir, pattern)
    
    # Search for the file
    matching_files = glob.glob(full_pattern)
    
    # Check if the file exists and get the first match
    if matching_files:
        return matching_files[0]
    else:
        return None

# Define the pattern for the file you are looking for
file_pattern = 'output_jsonl/transcript_0.jsonl'

# Get the file path
training_file_path = get_file_path(file_pattern)

def upload_file(file_name: str, purpose: str) -> str:
    with open(file_name, "rb") as file_fd:
        response = client.files.create(file=file_fd, purpose=purpose)
    return response.id


training_file_id = upload_file(training_file_path, "fine-tune")
# validation_file_id = upload_file(validation_file_name, "fine-tune")

print("Training file ID:", training_file_id)
# print("Validation file ID:", validation_file_id)

MODEL = "gpt-4o-mini-2024-07-18"

response = client.fine_tuning.jobs.create(
    training_file=training_file_id,
    # validation_file=validation_file_id,
    model=MODEL,
    suffix="initial-tune",
)

# job_id = response.id

# response = client.fine_tuning.jobs.retrieve(job_id)

print("Job ID:", response.id)
print("Status:", response.status)
print("Trained Tokens:", response.trained_tokens)

event_response = client.fine_tuning.jobs.list_events(response.id)

events = event_response.data
events.reverse()

for event in events:
    print(event.message)

retrieve_model_response = client.fine_tuning.jobs.retrieve(response.id)
fine_tuned_model_id = retrieve_model_response.fine_tuned_model

if fine_tuned_model_id is None:
    raise RuntimeError(
        "Fine-tuned model ID not found. Your job has likely not been completed yet."
    )

print("Fine-tuned model ID:", fine_tuned_model_id)

# use fine tuned model to generate response, commenting this out for now
# test_df = recipe_df.loc[201:300]
# test_row = test_df.iloc[0]
# test_messages = []
# test_messages.append({"role": "system", "content": system_message})
# user_message = create_user_message(test_row)
# test_messages.append({"role": "user", "content": user_message})

# pprint(test_messages)

# response = client.chat.completions.create(
#     model=fine_tuned_model_id, messages=test_messages, temperature=0, max_tokens=500
# )
# print(response.choices[0].message.content)