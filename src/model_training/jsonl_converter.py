import json
from src.config.constants import *
import os

current_dir = os.path.dirname(__file__)

relative_output_path = os.path.join(current_dir, '..', '..', 'cleaned_output', 'transcript_0_logging.json')

with open(relative_output_path, 'r') as f:
    data = json.load(f)

relative_jsonl_output_path = os.path.join(current_dir, '..', '..', 'output_jsonl', 'transcript_0_logging.jsonl')

# creating a jsonl file
with open(relative_jsonl_output_path, 'w') as outfile:
    for entry in data:
        
        text = entry.get('text', '')
        start_time = entry.get('start', 0)
        end_time = entry.get('end', 0)

        # checking if keyword or not
        if any(keyword in text.lower() for keyword in keywords):
            label = OPEN_AI_LABEL_1
        else:
            label = OPEN_AI_LABEL_2

        
        messages = [
            {"role": "system", "content": OPEN_AI_SYSTEM_MESSAGE},
            {"role": "user", "content": OPEN_AI_USER_INSTRUCTIONS},
            {"role": "assistant", "content": }
        ]

        # Create a JSON object for each entry
        json_obj = {"messages": messages}

        # Write to JSONL file
        outfile.write(json.dumps(json_obj) + "\n")

print("Conversion to JSONL with chat-like structure complete.")
