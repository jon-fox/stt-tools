from src.config.constants import *


class JSONLValidator:
    def __init__(self):
        self.format_errors = {
            "missing_messages_list": 0,
            "message_missing_key": 0,
            "message_unrecognized_key": 0,
            "unrecognized_role": 0,
            "missing_content": 0,
            "example_missing_assistant_message": 0
        }

    def validate(self, dataset):
        for ex in dataset:
            if not isinstance(ex, dict):
                self.format_errors["data_type"] += 1
                continue
                
            messages = ex.get("messages", None)
            if not messages:
                self.format_errors["missing_messages_list"] += 1
                continue
                
            for message in messages:
                if "role" not in message or "content" not in message:
                    self.format_errors["message_missing_key"] += 1
                
                if any(k not in ("role", "content", "name", "function_call", "weight") for k in message):
                    self.format_errors["message_unrecognized_key"] += 1
                
                if message.get("role", None) not in ("system", "user", "assistant", "function"):
                    self.format_errors["unrecognized_role"] += 1
                    
                content = message.get("content", None)
                function_call = message.get("function_call", None)
                
                if (not content and not function_call) or not isinstance(content, str):
                    self.format_errors["missing_content"] += 1
            
            if not any(message.get("role", None) == "assistant" for message in messages):
                self.format_errors["example_missing_assistant_message"] += 1

        if self.format_errors:
            print("Found errors:")
            for k, v in self.format_errors.items():
                print(f"{k}: {v}")
        else:
            print("No errors found")
            
        return self.format_errors