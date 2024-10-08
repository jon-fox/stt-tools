# stt_tools

This repository is intended as a library to manage tools for speech-to-text (STT) data and models using openai-python. 

## Environment Setup

To set up the environment, use the following command:

```bash
export PYTHONPATH=/mnt/c/Developer_Workspace/stt_tools/src:$PYTHONPATH

sudo apt install nvidia-cuda-toolkit # for faster whisper install https://github.com/SYSTRAN/faster-whisper/issues/516

pip install nvidia-cudnn-cu12

pip install ctranslate2

sudo find / -type f -iname '*libcudnn_ops_infer.so.8*'

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/mnt/c/Developer_Workspace/stt_tools/whisperxvenv/lib/python3.11/site-packages/nvidia/cudnn/lib/

## whisperx uses faster whisper in the backend
https://github.com/m-bain/whisperX

## Useful Links

| Description | Link |
|-------------|------|
| Hugging Face Audio Course | [Learn Audio Course](https://huggingface.co/learn/audio-course/en/chapter5/fine-tuning) |
| Faster Whisper Issue | [GitHub Issue #116](https://github.com/SYSTRAN/faster-whisper/issues/116) |
| OpenAI Fine-Tuning Examples | [Fine-Tuning Examples](https://platform.openai.com/docs/guides/fine-tuning/fine-tuning-examples) |
| OpenAI Data Formatting Guide | [Check Data Formatting](https://platform.openai.com/docs/guides/fine-tuning/check-data-formatting) |
| OpenAI Chat Fine-Tuning Data Preparation | [Chat Fine-Tuning Data Prep](https://cookbook.openai.com/examples/chat_finetuning_data_prep) |
| OpenAI How to Fine-Tune Chat Models | [How to Fine-Tune Chat Models](https://cookbook.openai.com/examples/how_to_finetune_chat_models) |
| OpenAI Structured Outputs in the API | [Introducing Structured Outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/) |