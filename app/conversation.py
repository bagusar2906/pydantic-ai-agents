from pydantic import BaseModel
from enum import Enum
from typing import List, ClassVar
import json
import os

# Define constants
DEFAULT_CONVERSATION_FILE = "conversation.json"
DEFAULT_REPLY_TYPE = "tool"

class ReplyType(Enum):
    ASSISTANT = "assistant"
    TOOL = "tool"

    def __str__(self):
        return self.value


class ChatModel(BaseModel):
    user: str
    reply_type: ReplyType
    reply_msg: str

    class Config:
        use_enum_values = True  # Use string values for enums instead of enum objects

    def to_dict(self):
        return self.dict()

    @staticmethod
    def from_dict(data):
        return ChatModel(**data)


class Conversation(BaseModel):
    chats: List[ChatModel]
    model_config: ClassVar = {
        "json_encoders": {
            ReplyType: lambda v: v.value
        }
    }

    def __init__(self, **data):
        super().__init__(**data)
        if not hasattr(self, 'chats'):
            self.chats = data.get('chats', [])
            self.chats = []
        if not isinstance(self.chats, list):
            raise TypeError("Expected 'chats' to be a list of Turn objects")

    # Method to add a Turn with string reply_type
    def add(self, user_msg: str, reply_type: str, reply_msg: str):
        # Convert reply_type string to ReplyType enum, defaulting to DEFAULT_REPLY_TYPE if invalid
        try:
            reply_type_enum = ReplyType(reply_type)
        except ValueError:
            reply_type_enum = ReplyType(DEFAULT_REPLY_TYPE)  # Default to DEFAULT_REPLY_TYPE if invalid

        # Create and append the new Turn
        new_chat = ChatModel(user=user_msg, reply_type=reply_type_enum, reply_msg=reply_msg)
        self.chats.append(new_chat)

    def get_reversed(self, limit: int = None) -> List[ChatModel]:
        reversed_pairs = self.chats[::-1]
        if limit is not None:
            reversed_pairs = reversed_pairs[:limit]
        return reversed_pairs

    def to_dict(self):
        return [chat.to_dict() for chat in self.chats]

    def to_json(self):
        return self.model_dump_json(indent=2)
    
    def clear(self):
        self.chats = []
        self.save_to_file(DEFAULT_CONVERSATION_FILE)
        print("Conversation cleared.")

    def save_to_file(self, file_path: str = DEFAULT_CONVERSATION_FILE):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"Conversation saved to '{file_path}'.")

    def chat_history(self, limit: int = None, skip: int = 0) -> List[List[str]]:
        raw = []
        chats = self.get_reversed(limit)[skip:]  # Skip the first `n` chats
        for chat in chats:
            raw.append(["user", chat.user])
            raw.append(["assistant", chat.reply_msg])
            # if chat.reply_type == ReplyType.ASSISTANT.value or chat.reply_type == ReplyType.TOOL.value:
            #     raw.append([chat.reply_type, chat.reply_msg])
            # else:
            #     raw.append([DEFAULT_REPLY_TYPE, chat.reply_msg])
        return raw
        #return json.dumps(raw, indent=2)
        
    def load_from_file(self, file_path: str = DEFAULT_CONVERSATION_FILE):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_conversation = self.auto_load_json(f.read())
                self.chats = loaded_conversation.chats  # Update the chats attribute
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in file: {file_path}")

    @staticmethod
    def auto_load_json(json_str: model_config) -> "Conversation": # type: ignore
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON format") from e

        # Case 1: Full Conversation object
        if isinstance(parsed, dict) and "turns" in parsed:
            return Conversation.model_validate(parsed)

        # Case 2: Flat list of Turn dicts
        if isinstance(parsed, list):
            if not all(isinstance(d, dict) for d in parsed):
                raise TypeError("Expected list of dictionaries for flat turn list")
            return Conversation(chats=[ChatModel(**d) for d in parsed])

        raise TypeError("Unsupported JSON structure for Conversation")
