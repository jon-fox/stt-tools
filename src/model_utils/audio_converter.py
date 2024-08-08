from pydub import AudioSegment
import whisper_timestamped as whisper
import concurrent.futures
import json
import os
import re
import time
from queue import Queue
from src.config.constants import *
from src.utils.logger_setup import logger
from src.config.constants import keywords, KI_TXT_PATH

# adding some buffers to catch anything
START_KEYWORD_BUFFER = 15
END_KEYWORD_BUFFER = 15

import threading
# lock = threading.Lock()
# lock = threading.RLock()



# compiled regex patterns for keywords
keywords_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in keywords]

# Specify the relative path to the file
import os

script_dir = os.path.dirname(os.path.realpath(__file__))

# Get the current working directory
cwd = os.getcwd()
logger.info(f'Current working directory: {cwd}')

with open(KI_TXT_PATH, 'r') as file:
    key_indicators = {line.strip().lower() for line in file}


# Find positions of keyword-related keywords in the transcription
def find_keyword_timestamps(transcript):
    """
    Find the timestamps of keyword segments in a transcription.

    Args:
        transcription (dict): The transcription data containing segments.

    Returns:
        tuple: A tuple containing the keyword timestamps dictionary, 
        the minimum start time, and the maximum end time.

    The keyword timestamps dictionary has the following structure:
    {
        'keyword1': [[start1, end1], [start2, end2], ...],
        'keyword2': [[start1, end1], [start2, end2], ...],
        ...
    }
    The minimum start time and maximum end time represent 
    the overall time range of the keywordsegments found.
    """

    # Assuming transcript is a dictionary
    # keys = list(transcript[0].keys())
    # logger.info("############################################")
    # logger.info(f"First few of transcript keys: {keys[:1]}")
    # logger.info(f"Transcript: {transcript}")
    # logger.info("############################################")

    min_ms = float('inf')  # Positive infinity
    max_ms = float('-inf')  # Negative infinity

    # for logging
    current_block = None

    # TODO need to capture the words that kicked off the keywordsegment
    for t_segment in transcript:
        text = t_segment['text'].lower()

        # high_certainty = any(ki.lower() in text for ki in key_indicators)

        contains_ki = any(ki in text for ki in key_indicators) or \
                any(pattern.search(text) for pattern in keywords_compiled)

        if contains_ki:
            start = max(0, t_segment['start'] - START_KEYWORD_BUFFER)
            end = t_segment['end'] + END_KEYWORD_BUFFER

            # logging keyword segment keywords to file
            # with open("keywords.txt", "a") as file:
            #     file.write(text + '\n' + f'{start} - {end}\n\n')

            if current_block is None:
                current_block = [start, end]
            else:
                # Extend the current keywordblock if overlapping or adjacent within buffer
                if start <= current_block[1]:
                    current_block[1] = max(current_block[1], end)
                else:
                    # Update overall min and max if current block is finalized
                    min_ms = min(min_ms, current_block[0])
                    max_ms = max(max_ms, current_block[1])
                    current_block = [start, end]
        else:
            if current_block is not None:
                # Update overall min and max if moving out of keywordsegment
                min_ms = min(min_ms, current_block[0])
                max_ms = max(max_ms, current_block[1])
                current_block = None

    # Final update at the end of the transcript
    if current_block is not None:
        min_ms = min(min_ms, current_block[0])
        max_ms = max(max_ms, current_block[1])
    return min_ms, max_ms

def extract_segments(segments, start_time, end_time):
    """Extracts segments from a JSON string based on the given start and end times.

    Args:
        json_string (str): The JSON string containing the segments.
        start_time (float): The start time of the desired segments.
        end_time (float): The end time of the desired segments.

    Returns:
        list: A list of extracted segments that fall within the specified time range.
    """
    # data = json.loads(json_string)
    # segments = data['segments']
    extracted_segments = [segment for segment in segments if start_time <= segment['start'] <= end_time]
    return extracted_segments

# Initialize model_pool at the module level
model_pool = Queue()

def initialize_model_pool(device="cuda"):
    """
    Initializes a pool of Whisper models.

    Parameters:
    - device: The device to load the models on. Defaults to 'cuda'.

    Returns:
    - A queue.Queue object containing the loaded Whisper models.
    """
    global model_pool
    for _ in range(NUMBER_OF_MODELS):
        model_file_path = os.path.join(MODEL_DOWNLOAD_PATH, MODEL_FILE_NAME)
        logger.info(f"Checking Model file path: {model_file_path}")
        if os.path.isfile(model_file_path):
            logger.info(f"Loading model from file: {model_file_path}")
            whisper_model = whisper.load_model(model_file_path, device=device)
        else:
            logger.info(f"Downloading model from Hugging Face model hub")
            whisper_model = whisper.load_model("tiny", download_root=os.path.join(MODEL_DOWNLOAD_PATH), device=device)
            # model = whisper.load_model("tiny", device=device)
        # model = whisper.load_model("tiny", device="cpu")
        model_pool.put(whisper_model)


def process_audio_segment(index, audio_segment):
    try:
        model = model_pool.get(block=True) # Wait until a model is available
        logger.info(f"Thread using model {id(model)}")
        segment_path = f"segment_{index}.wav"
        audio_segment.export(segment_path, format="wav")
        result = whisper.transcribe(model, segment_path, language="en")
        # Clean up segment file after use
        # logger.info(f"Finding Timestamps for segment index {index}")
        min_ms, max_ms = find_keyword_timestamps(result["segments"])
        # Return the model to the pool
        model_pool.put(model)
    except Exception as e:
        import traceback
        logger.error(traceback.print_exc())
        raise Exception(f"An error occurred during Transcription: {str(e)}")

    # logger.info(f"keywordtimestamps: {keyword_timestamps}")
    logger.info(f"##############################################")
    logger.info(f"Segment {index}")
    logger.info(f"min_ms: {min_ms}, max_ms: {max_ms}")
    logger.info(f"##############################################")

    # Slice audio before and after the keyword
    os.remove(segment_path)
    if min_ms == float('inf') and max_ms == float('-inf'):
        logger.info("No keywords found in the segment")
    elif max_ms - min_ms < 20:
        logger.info("Skipping segment with less than 20 seconds of keywords, likely false positive")
    else:
        # TODO commented out for now, need to test transcript logging
        # if max_ms - min_ms > 360:
        #     logger.info("keyword segment is over 6 minutes, likely false positive. Reducing to 5 minutes")
            # max_ms = min_ms + 300
            # logger.info(f"SETTING::: min_ms: {min_ms}, max_ms: {max_ms}")
        # Extract the segments containing keywords for logging
        segments = extract_segments(result["segments"], min_ms, max_ms)

        ################################################################

        with open(f"{script_dir}/transcript_{index}_logging.json", "w", encoding="utf-8") as file:
            logger.info(f"Logging keyword segments to {script_dir}/transcript_{index}_logging.json")
            json.dump(segments, file, indent=2, ensure_ascii=False)

        if min_ms == float('inf') and max_ms == float('-inf'):
            logger.info("No keywords found in the segment")

        ################################################################


def find_keywords_from_audio(audio_file):
    """
    Removes keywords from an audio file.

    This function takes an MP3 audio file as input, splits it into 10-minute segments,
    transcribes each segment, identifies keyword timestamps in the transcription, and removes
    the corresponding audio segments containing the keywords. The resulting audio file without
    keywords is saved as "finished_audio_without_keywords.mp3".

    Note: This function requires the 'whisper' library and the 'AudioSegment' class from
    the 'pydub' library.

    Args:
        None

    Returns:
        None
    """
    wav_file = "result.wav"

    audio = AudioSegment.from_mp3(audio_file)
    original_duration = len(audio) / 1000

    audio.export(wav_file, format="wav")

    # Load the WAV file
    audio = AudioSegment.from_wav(wav_file)

    # Duration of each segment in milliseconds (10 minutes)
    segment_duration_ms = 10 * 60 * 1000

    # Duration of audio in milliseconds
    duration_ms = len(audio)

    # Split audio into 10-minute segments
    segments = [audio[i:i + segment_duration_ms] for i in range(0, duration_ms, segment_duration_ms)]

    logger.info(f"Initializing Model Pool with {NUMBER_OF_MODELS} models")
    initialize_model_pool(device="cpu")

    # Using ThreadPoolExecutor to process each segment
    with concurrent.futures.ThreadPoolExecutor(max_workers=model_pool.qsize()) as executor:
        logger.info(f"Using {model_pool.qsize()} models for processing")
        # Submit all segments to the executor
        future_to_segment = {executor.submit(process_audio_segment, i, segments[i]): i for i in range(len(segments))}
        
        # Collect results as they complete
        results = []
        for future in concurrent.futures.as_completed(future_to_segment):
            segment_index = future_to_segment[future]
            logger.info(f"Processing segment for segment index {segment_index}")
            try:
                result = future.result()
                results.append((segment_index, result))  # Store results along with their original index
            except Exception as exc:
                logger.error(f"Segment {segment_index} generated an exception: {exc}")
                import traceback
                traceback.print_exc()
    logger.info(f"Finished processing all segments, original duration of processed audio: {original_duration}")
