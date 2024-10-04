from src.config.constants import *
import glob
import os
import openai
from src.model_validator.call_fine_tuned_model import FineTunedModelCaller
from src.s3_utils.upload_transcripts import upload_directory_to_bucket
from src.audio_tools.audio_converter_faster import find_keywords_from_audio

def fine_tune_model():
    api_key=os.environ.get("OPENAI_API_KEY")
    organization=os.environ.get("OPENAI_ORG_ID")
    project=os.environ.get("OPENAI_PROJECT_ID")

    model_caller = FineTunedModelCaller(
        api_key=api_key, 
        org_id=organization, 
        project_id=project, 
        # transcript_file_path="/mnt/c/Developer_Workspace/stt_tools/output/transcript_0_logging.json",
        transcript_file_path="/mnt/c/Developer_Workspace/stt_tools/output/transcript_3_logging.json",
        fine_tuned_model_id=FINE_TUNED_MODEL_ID
    )

    model_caller.call_model(OPEN_AI_USER_INSTRUCTIONS.replace("{CONFIDENCE_SCORE}", str(CONFIDENCE_SCORE)))
    paths = [
        {
            "source_directory":"/mnt/c/Developer_Workspace/stt_tools/output/",
            "target_directory": "transcripts/darknet_diaries/raw_transcripts/"
        },
        {
            "source_directory": "/mnt/c/Developer_Workspace/stt_tools/cleaned_output/",
            "target_directory": "transcripts/darknet_diaries/cleaned_transcripts/"
        },
        {
            "source_directory": "/mnt/c/Developer_Workspace/stt_tools/output_jsonl/",
            "target_directory": "transcripts/darknet_diaries/jsonl_examples/"
        }
    ]

    for path in paths:
        source_directory = path["source_directory"]
        target_directory = path["target_directory"]
        upload_directory_to_bucket(source_directory, target_directory)


if __name__ == '__main__':
    # fine_tune_model()

    audio_file_path = DOWNLOAD_DIR + "sample.mp3"

    find_keywords_from_audio(audio_file_path)
