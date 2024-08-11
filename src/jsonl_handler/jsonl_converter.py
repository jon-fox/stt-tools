import json
from src.config.constants import *
import os
import glob

class JSONLConverter:
    def __init__(self, output_jsonl_name="transcript_0.jsonl"):
        self.current_dir = os.path.dirname(__file__)
        self.cleaned_output_dir = os.path.join(self.current_dir, '..', '..', 'cleaned_output')
        self.jsonl_output_dir = os.path.join(self.current_dir, '..', '..', 'output_jsonl')
        self.output_file_path = os.path.join(self.jsonl_output_dir, output_jsonl_name)
        self.json_files = glob.glob(os.path.join(self.cleaned_output_dir, '*.json'))
        self.filtered_files = [f for f in self.json_files if 'meta' not in os.path.basename(f)]
        self.meta_files = [f for f in self.json_files if 'meta' in os.path.basename(f)]


    def find_meta_file(self, filtered_file):
        base_name = os.path.basename(filtered_file)
        meta_file_name = f"{os.path.splitext(base_name)[0]}_meta.json"
        meta_file_path = os.path.join(self.cleaned_output_dir, meta_file_name)
        return meta_file_path if meta_file_path in self.meta_files else None


    # creating jsonl files for each filtered file
    def convert(self):
        with open(self.output_file_path, 'a') as outfile:
            for file_path in self.filtered_files:
                #output file path
                meta_file_path = self.find_meta_file(file_path)

                # opening transcript file, meta file and output file
                with open(file_path, 'r') as infile:
                    data = json.load(infile)
                    meta_data = {}
                    if meta_file_path:
                        with open(meta_file_path, 'r') as metafile:
                            meta_data = json.load(metafile)
                    
                    # https://jsonlines.org/validator/

                    messages = [
                        {"role": "system", "content": OPEN_AI_SYSTEM_MESSAGE},
                        {"role": "user", "content": f"{OPEN_AI_USER_INSTRUCTIONS}|Transcript:{data}"},
                        {"role": "assistant", "content": f"{meta_data['expected_response']}"}
                    ]

                    json_obj = {"messages": messages}

                    # Write to the output file
                    outfile.write(json.dumps(json_obj) + "\n")

        print("Conversion to JSONL with chat-like structure complete.")
