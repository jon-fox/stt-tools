from pprint import pprint
from src.config.constants import *
import openai
import os
import glob
import time

class EventHandler():
    def __init__(self):
        # super().__init__()
        self.results = {}

    # @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)

    # @override
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    # @override
    def on_message_done(self, client, message) -> None:
        # print a citation to the file searched
        # print(f"On Message Done: {message}")
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(
                annotation.text, f"[{index}]"
            )
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")

        print(f"Message content value:: {message_content.value}")
        # print("##############################################")
        self.results['message'] = message_content.value
        print(f"Results: {self.results['message']}")
        self.results['citations'] = citations

class FineTunedModelCaller:
    def __init__(self, api_key, org_id, project_id, transcript_file_path, fine_tuned_model_id):
        self.client = openai.OpenAI(
            api_key=api_key,
            organization=org_id,
            project=project_id,
        )
        self.transcript_file_path = transcript_file_path
        self.fine_tuned_model_id = fine_tuned_model_id

    def get_file_paths(self):
        # Assuming transcript_file_path is a directory or a pattern
        if os.path.isdir(self.transcript_file_path):
            return glob.glob(os.path.join(self.transcript_file_path, self.file_pattern))
        else:
            return glob.glob(self.transcript_file_path)

    def _create_thread(self, user_instructions, assistant_id):

        vector_name = self.transcript_file_path.split("/")[-1]
        vector_store = self.client.beta.vector_stores.create(name=vector_name)

        file_paths = self.get_file_paths()
        print(f"File Paths: {file_paths}")
        file_streams = [open(path, "rb") for path in file_paths]

        # Use the upload and poll SDK helper to upload the files, add them to the vector store,
        # and poll the status of the file batch for completion.
        file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=file_streams
        )

        print(file_batch.status)
        print(file_batch.file_counts)

        assistant = self.client.beta.assistants.update(
            assistant_id=assistant_id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )
        
        # print(f"File ID: {message_file.id}, Created for file: {filename} and path: {path}")
        print(f"File ID: {file_batch.id}, Created for file: {self.transcript_file_path}")

        # Create a thread and attach the file to the message
        thread = self.client.beta.threads.create(
            messages=[
                    {
                        "role": "user",
                        "content": user_instructions,
                    }
                ],
            tool_resources={
                "file_search": {
                "vector_store_ids": [vector_store.id]
                }
            }
        )

        print(f"Thread ID: {thread.id}, Created for file: {self.transcript_file_path}")
        
        # The thread now has a vector store with that file in its tool resources.
        # print(thread.tool_resources.file_search)

        return thread
    
    def _create_assistant(self, system_message=OPEN_AI_SYSTEM_MESSAGE):
        assistant = self.client.beta.assistants.create(
            name="Podcast Advertisement Recognizer",
            instructions=system_message,
            tools=[{"type": "file_search"}],
            temperature=0,
            model=self.fine_tuned_model_id,
        )
        return assistant.id
    
    def _retrieve_assistant(self, assistant_id=None):
        print(f"Retrieving assistant...")
        response = self.client.beta.assistants.list()

        if not assistant_id:
            print(f"Assistant Not Found in Var Cache retrieving assistant...")
            for assistant in response.data:
                print(f"Assistant Found: {assistant.id}")
                # client.beta.assistants.retrieve(assistant.id)
                assistant_id = assistant.id
                return assistant_id
            else:
                print("No assistant found, creating assistant...")
                assistant_id = self._create_assistant()
                return assistant_id
        return assistant_id

    def call_model(self, user_instructions):
        assistant_id = self._retrieve_assistant()
        
        thread = self._create_thread(user_instructions, assistant_id)

        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        ) 

        while run.status.lower() in ["queued", "in_progress"]:
            retrieving_thread_run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )

            print(f"Run status: {retrieving_thread_run.status}")

            if retrieving_thread_run.status.lower() == "completed":
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id,
                    run_id=run.id
                )
                # print(f"Messages: {messages.data}")
                event_handler=EventHandler()
                event_handler.on_message_done(self.client, messages.data[0])
                print("\n")
                # Step 6: Retrieve the Messages added by the Assistant to the Thread
                print(f"#########################################################")
                print(f"printing for file: {self.transcript_file_path}")
                print(event_handler.results)
                print(f"#########################################################")
                message = event_handler.results['message']
                break
            elif retrieving_thread_run.status == "queued" or retrieving_thread_run.status == "in_progress":
                time.sleep(5)
                pass
            else:
                print(f"Run status: {retrieving_thread_run.status}")
                print(f"Run failed for file: {self.transcript_file_path}")
                print(f"Run output: {retrieving_thread_run}")
                break
