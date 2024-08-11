from pprint import pprint
from src.config.constants import *
import openai
import os
import glob
import time

client = openai.OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    organization=os.environ.get("OPENAI_ORG_ID"),
    project=os.environ.get("OPENAI_PROJECT_ID"),
)

assistant = client.beta.assistants.create(
    name="Podcast Advertisement Recognizer",
    instructions=OPEN_AI_SYSTEM_MESSAGE,
    tools=[{"type": "file_search"}],
    temperature=0,
    model=FINE_TUNED_MODEL_ID,
)

def _create_thread(filename, path):
  thread = client.beta.threads.create()

  vector_store = client.beta.vector_stores.create(name=filename)

  file_paths = [path]
  file_streams = [open(path, "rb") for path in file_paths]

   # Use the upload and poll SDK helper to upload the files, add them to the vector store,
   # and poll the status of the file batch for completion.
  file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store.id, files=file_streams
  )

  print(file_batch.status)
  print(file_batch.file_counts)

  assistant = client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
  )
  
  # print(f"File ID: {message_file.id}, Created for file: {filename} and path: {path}")
  print(f"File ID: {file_batch.id}, Created for file: {filename} and path: {path}")

  # Create a thread and attach the file to the message
  thread = client.beta.threads.create(
    messages=[
      {
        "role": "user",
        "content": OPEN_AI_USER_INSTRUCTIONS,
      }
    ],
        tool_resources={
          "file_search": {
          "vector_store_ids": [vector_store.id]
          }
      }
  )

  print(f"Thread ID: {thread.id}, Created for file: {filename} and path: {path}")
 
  # The thread now has a vector store with that file in its tool resources.
  # print(thread.tool_resources.file_search)

  return thread

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
file_pattern = 'output/transcript_0_logging.json'

# Get the file path
transcript_file_path = get_file_path(file_pattern)

def upload_file(file_name: str, purpose: str) -> str:
    with open(file_name, "rb") as file_fd:
        response = client.files.create(file=file_fd, purpose=purpose)
    return response.id

training_file_id = upload_file(transcript_file_path, "assistants")

test_messages = [
    {"role": "system", "content": OPEN_AI_SYSTEM_MESSAGE},
    {"role": "user", "content": f"{OPEN_AI_USER_INSTRUCTIONS}|Transcript:{data}"},
    # {"role": "assistant", "content": f"{meta_data['expected_response']}"}
]


thread = _create_thread(filename="transcript_0_logging.json", path=transcript_file_path)

run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
)

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
    def on_message_done(self, message) -> None:
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


while run.status.lower() in ["queued", "in_progress"]:
    retrieving_thread_run = client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id,
    )

    print(f"Run status: {retrieving_thread_run.status}")

    if retrieving_thread_run.status.lower() == "completed":
        messages = client.beta.threads.messages.list(
        thread_id=thread.id,
        run_id=run.id
        )
        # print(f"Messages: {messages.data}")
        event_handler=EventHandler()
        event_handler.on_message_done(messages.data[0])
        print("\n")
        # Step 6: Retrieve the Messages added by the Assistant to the Thread
        print(f"#########################################################")
        print(f"printing for file: {file_pattern}, and path: {transcript_file_path}")
        print(event_handler.results)
        print(f"#########################################################")
        message = event_handler.results['message']
    elif retrieving_thread_run.status == "queued" or retrieving_thread_run.status == "in_progress":
        time.sleep(5)
        pass
    else:
        print(f"Run status: {retrieving_thread_run.status}")
        print(f"Run failed for file: {file_pattern} and path: {transcript_file_path}")
        print(f"Run output: {retrieving_thread_run}")
        print("No timestamps provided. Returning None.")

