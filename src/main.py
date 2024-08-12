from src.config.constants import *
import glob
import os
import openai
from src.model_validator.call_fine_tuned_model import FineTunedModelCaller

if __name__ == '__main__':
    
    api_key=os.environ.get("OPENAI_API_KEY")
    organization=os.environ.get("OPENAI_ORG_ID")
    project=os.environ.get("OPENAI_PROJECT_ID")

    model_caller = FineTunedModelCaller(
        api_key=api_key, 
        org_id=organization, 
        project_id=project, 
        transcript_file_path="/mnt/c/Developer_Workspace/stt_tools/output/transcript_0_logging.json",
        fine_tuned_model_id=FINE_TUNED_MODEL_ID
    )

    model_caller.call_model(OPEN_AI_USER_INSTRUCTIONS.replace("{CONFIDENCE_SCORE}", str(CONFIDENCE_SCORE)))

    
