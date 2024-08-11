import tiktoken # for token counting
import numpy as np
import os
import json
from src.config.constants import *


class TokenCounter:
    def __init__(self, dataset_path, encoding="cl100k_base", char_limit=65536):
        self.dataset_path = dataset_path
        self.dataset = self.load_dataset()
        self.encoding = tiktoken.get_encoding(encoding_name=encoding)
        self.char_limit = char_limit
        self.n_missing_system = 0
        self.n_missing_user = 0
        self.n_messages = []
        self.convo_lens = []
        self.assistant_message_lens = []

    class Response:
        def __init__(self, num_tokens=0, n_too_long=0, examples_with_errors={}, n_missing_system=0, n_missing_user=0, n_messages=[], convo_lens=[], assistant_message_lens=[]):
            self.num_tokens = num_tokens
            self.n_too_long = n_too_long
            self.examples_with_errors = examples_with_errors
            self.n_missing_system = n_missing_system
            self.n_missing_user = n_missing_user
            self.n_messages = n_messages
            self.convo_lens = convo_lens
            self.assistant_message_lens = assistant_message_lens

    # Load the dataset
    def load_dataset(self):
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            return [json.loads(line) for line in f]

    # simplified from https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    def num_tokens_from_messages(self, messages, tokens_per_message=3, tokens_per_name=1):
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(self.encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3
        return num_tokens

    def num_assistant_tokens_from_messages(self, messages):
        num_tokens = 0
        for message in messages:
            if message["role"] == "assistant":
                num_tokens += len(self.encoding.encode(message["content"]))
        return num_tokens

    def print_distribution(self, values, name):
        print(f"\n#### Distribution of {name}:")
        print(f"min / max: {min(values)}, {max(values)}")
        print(f"mean / median: {np.mean(values)}, {np.median(values)}")
        print(f"p5 / p95: {np.quantile(values, 0.1)}, {np.quantile(values, 0.9)}")

    # Warnings and tokens counts
    def get_warnings_and_token_counts(self):
        response = self.Response()
        for ex in self.dataset:
            messages = ex["messages"]
            if not any(message["role"] == "system" for message in messages):
                response.examples_with_errors.setdefault(f"example_{i}", []).append("missing_system_message")
                self.n_missing_system += 1
            if not any(message["role"] == "user" for message in messages):
                response.examples_with_errors.setdefault(f"example_{i}", []).append("missing_user_message")
                self.n_missing_user += 1
            self.n_messages.append(len(messages))
            self.convo_lens.append(self.num_tokens_from_messages(messages))
            self.assistant_message_lens.append(self.num_assistant_tokens_from_messages(messages))
            
        print("Num examples missing system message:", self.n_missing_system)
        print("Num examples missing user message:", self.n_missing_user)
        self.print_distribution(self.n_messages, "num_messages_per_example")
        self.print_distribution(self.convo_lens, "num_total_tokens_per_example")
        self.print_distribution(self.assistant_message_lens, "num_assistant_tokens_per_example")

        n_too_long = 0

        # Iterate through convo_lens and print the corresponding lines that exceed the limit
        for i, length in enumerate(self.convo_lens):
            if length > self.char_limit:
                char_limit_error = f"Example {i} exceeds the {self.char_limit} token limit, actual length is {length}:"
                print(char_limit_error)
                last_100_chars = json.dumps(self.dataset[i])[-100:]
                print(f"Last 100 characters of Example {i}: {last_100_chars}")
                print("\n")
                response.examples_with_errors.setdefault(f"example_{i}", []).append(char_limit_error)
                n_too_long += 1
        
        response.n_too_long = n_too_long
        response.n_messages = self.n_messages
        response.n_missing_system = self.n_missing_system
        response.n_missing_user = self.n_missing_user
        response.convo_lens = self.convo_lens
        response.assistant_message_lens = self.assistant_message_lens

        print(f"\n{n_too_long} examples may be over the {self.char_limit} token limit, they will be truncated during fine-tuning")

        return response
