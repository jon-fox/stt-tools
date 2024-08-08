from src.model_utils.audio_converter import find_keywords_from_audio
from src.config.constants import DOWNLOAD_DIR
import glob

if __name__ == '__main__':
    
    mp3_files = glob.glob(f'{DOWNLOAD_DIR}*.mp3')
    
    for mp3_file in mp3_files:
        find_keywords_from_audio(mp3_file)
