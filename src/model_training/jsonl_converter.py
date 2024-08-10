import json
from src.config.constants import *
import os
import glob

current_dir = os.path.dirname(__file__)

cleaned_output_dir = os.path.join(current_dir, '..', '..', 'cleaned_output')

# getting all JSON files in the cleaned_output directory
json_files = glob.glob(os.path.join(cleaned_output_dir, '*.json'))

# filter out files that contain 'meta' in their names
filtered_files = [f for f in json_files if 'meta' not in os.path.basename(f)]

meta_files = [f for f in json_files if 'meta' in os.path.basename(f)]

def find_meta_file(filtered_file):
    base_name = os.path.basename(filtered_file)
    meta_file_name = f"{os.path.splitext(base_name)[0]}_meta.json"
    meta_file_path = os.path.join(cleaned_output_dir, meta_file_name)
    return meta_file_path if meta_file_path in meta_files else None

# creating jsonl files for each filtered file
for file_path in filtered_files:
    #output file path
    base_name = os.path.basename(file_path)
    output_file_name = f"{os.path.splitext(base_name)[0]}_output.jsonl"
    output_file_path = os.path.join(current_dir, '..', '..', 'output_jsonl', output_file_name)

    meta_file_path = find_meta_file(file_path)

    # opening transcript file, meta file and output file
    with open(file_path, 'r') as infile, open(output_file_path, 'w') as outfile:
        data = json.load(infile)
        meta_data = {}
        if meta_file_path:
            with open(meta_file_path, 'r') as metafile:
                meta_data = json.load(metafile)
        
        # https://jsonlines.org/validator/

        messages = [
            {"role": "system", "content": OPEN_AI_SYSTEM_MESSAGE},
            {"role": "user", "content": f"{OPEN_AI_USER_INSTRUCTIONS}|Transcript:{data}"},
            {"role": "assistant", "content": meta_data['expected_response']}
        ]

        json_obj = {"messages": messages}

        # Write to the output file
        outfile.write(json.dumps(json_obj) + "\n")

print("Conversion to JSONL with chat-like structure complete.")
