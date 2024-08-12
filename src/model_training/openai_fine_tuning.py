import json
import openai
import os
# import pandas as pd
from pprint import pprint
from src.config.constants import *
import glob


class OpenAIFineTuner:
    def __init__(self, api_key, org_id, project_id, model, file_pattern):
        self.client = openai.OpenAI(
            api_key=api_key,
            organization=org_id,
            project=project_id,
        )
        self.model = model
        self.file_pattern = file_pattern
        self.training_file_path = self._get_file_path(file_pattern)

    def _get_file_path(self, pattern):
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        full_pattern = os.path.join(base_dir, pattern)
        matching_files = glob.glob(full_pattern)
        return matching_files[0] if matching_files else None

    def _upload_file(self, file_name: str, purpose: str) -> str:
        with open(file_name, "rb") as file_fd:
            response = self.client.files.create(file=file_fd, purpose=purpose)
        return response.id
    
    def _get_fine_tuned_model(self, response, checks=5):
        print("Job ID:", response.id)
        print("Status:", response.status)
        print("Trained Tokens:", response.trained_tokens)

        event_response = self.client.fine_tuning.jobs.list_events(response.id)
        events = event_response.data
        events.reverse()

        for event in events:
            print(event.message)

        while True:
            retrieve_model_response = self.client.fine_tuning.jobs.retrieve(response.id)
            fine_tuned_model_id = retrieve_model_response.fine_tuned_model
            if fine_tuned_model_id:
                print("Fine-tuned model ID:", fine_tuned_model_id)
                return fine_tuned_model_id
            elif fine_tuned_model_id is None and checks == 0:
                raise RuntimeError(
                    f"Fine-tuned model ID not found. Job has not completed may have errors. Checks {checks}"
                )
            checks -= 1

    def fine_tune(self):
        training_file_id = self._upload_file(self.training_file_path, "fine-tune")
        print("Training file ID:", training_file_id)

        response = self.client.fine_tuning.jobs.create(
            training_file=training_file_id,
            model=self.model,
            suffix="initial-tune",
        )

        fine_tuned_model_id = self._get_fine_tuned_model(response)
        return fine_tuned_model_id
