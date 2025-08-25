import json
import logging
import re
from typing import Any, List

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ClientMessage(BaseModel):
    id: str
    role: str
    parts: List[dict[str, Any]]


def convert_to_messages(messages: List[ClientMessage]):
    converted_messages = []

    for message in messages:
        parts = message.parts
        contents = []

        for part in parts:
            part_type: str = part.get("type", "")

            if part_type == "file":
                media_type: str = part.get("mediaType", "")
                filename: str = part.get("filename", "")
                url: str = part.get("url", "")

                if media_type.startswith("image"):
                    match = re.match(r"data:([^;]+);base64,(.+)", url)

                    if match:
                        mime_type = match.group(1)
                        data = match.group(2)
                        file_format = mime_type.split("/")[1]

                        contents.append(
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": data,
                                },
                            }
                        )
                elif media_type.startswith("text"):
                    match = re.match(r"data:([^;]+);base64,(.+)", url)

                    if match:
                        mime_type = match.group(1)
                        data = match.group(2)
                        file_format = mime_type.split("/")[1]

                        contents.append(
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "format": file_format,
                                        "name": filename,
                                        "source": {
                                            "type": "base64",
                                            "media_type": mime_type,
                                            "data": data,
                                        },
                                    },
                                    ensure_ascii=False,
                                ),
                            }
                        )

            elif part_type.startswith("tool-"):
                tool_id = part.get("toolCallId")
                tool_name = part_type.removeprefix("tool-")
                tool_input = part.get("input")
                tool_output = part.get("output")

                contents.append(
                    {
                        "type": "tool_use",
                        "id": tool_id,
                        "name": tool_name,
                        "input": tool_input,
                    }
                )

                if bool(tool_output):
                    contents.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(tool_output),
                        }
                    )
            elif part_type == "text":
                contents.append(part)

        if bool(contents):
            converted_messages.append({"role": message.role, "content": contents})

    return converted_messages


if __name__ == "__main__":
    url = "data:text/plain;base64,dGVzdCBjb250ZW50IGZpbGVzLgp0aGlzIGlzIGEgZ29vZCBmaWxlLgo="
    match = re.match(r"data:([^;]+);base64,(.+)", url)
    if match:
        mime_type = match.group(1)
        data = match.group(2)
        print(mime_type)
        print(data)
