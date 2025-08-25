import json
import logging
from typing import Any, List

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from langchain_aws import ChatBedrock
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from pydantic import BaseModel

from api.utils.message import (
    DataPart,
    StreamingData,
    TextDeltaPart,
    TextEndPart,
    TextStartPart,
    ToolInputAvailablePart,
    ToolInputDeltaPart,
    ToolInputStartPart,
    ToolOutputAvailablePart,
)

from .utils.prompt import ClientMessage, convert_to_messages
from .utils.tools import get_current_weather

logger = logging.getLogger(__name__)

load_dotenv(".env.local")

app = FastAPI()

model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"
config = {
    "max_tokens": 4096,
    "temperature": 0,
    "top_p": 0.999,
    "top_k": 256,
}


client = ChatBedrock(
    region="us-east-1",
    model_id=model_id,
    model_kwargs=config,
)

tools = [get_current_weather]
client_with_tools = client.bind_tools(tools, tool_choice="auto")


def stream_text(messages: List[dict[str, Any]], protocol: str = "data"):
    stream = client_with_tools.stream(input=messages)

    # When protocol is set to "text", you will send a stream of plain text chunks
    # https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#text-stream-protocol

    if protocol == "text":
        for chunk in stream:
            if not isinstance(chunk, BaseMessage):
                continue

            stop_reason = chunk.response_metadata.get("stop_reason")

            if stop_reason == "end_turn":
                break
            else:
                yield "{text}".format(text=chunk.text())

    # When protocol is set to "data", you will send a stream data part chunks
    # https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#data-stream-protocol

    elif protocol == "data":
        draft_tool_calls = []
        draft_tool_calls_index = -1

        is_message_started = False
        is_text_started = False

        for chunk in stream:
            if not isinstance(chunk, BaseMessage):
                continue

            message_id = chunk.id
            stop_reason = chunk.response_metadata.get("stop_reason")

            if not is_message_started:
                yield StreamingData.start(message_id).dump()
                is_message_started = True

            if stop_reason == "end_turn":
                continue

            elif stop_reason == "tool_use":
                if is_text_started:
                    yield StreamingData(data=TextEndPart(id=message_id)).dump()
                    is_text_started = False

                for tool_call in draft_tool_calls:
                    yield StreamingData(
                        data=ToolInputAvailablePart(
                            toolCallId=tool_call["id"],
                            toolName=tool_call["name"],
                            input=json.loads(tool_call["arguments"]),
                        )
                    ).dump()

                for tool_call in draft_tool_calls:
                    tool_result = get_current_weather.invoke(
                        input=json.loads(tool_call["arguments"])
                    )

                    yield StreamingData(
                        data=ToolOutputAvailablePart(
                            toolCallId=tool_call["id"],
                            toolName=tool_call["name"],
                            output=tool_result,
                        )
                    ).dump()

            elif isinstance(chunk, AIMessageChunk) and bool(chunk.tool_call_chunks):
                if is_text_started:
                    yield StreamingData(data=TextEndPart(id=message_id)).dump()
                    is_text_started = False

                for tool_call in chunk.tool_call_chunks:
                    id = tool_call.get("id")
                    name = tool_call.get("name")
                    arguments = tool_call.get("args")

                    if id is not None:
                        draft_tool_calls_index += 1
                        draft_tool_calls.append(
                            {"id": id, "name": name, "arguments": ""}
                        )
                        yield StreamingData(
                            data=ToolInputStartPart(toolCallId=id, toolName=name)
                        ).dump()
                    else:
                        draft_tool_calls[draft_tool_calls_index]["arguments"] += (
                            arguments
                        )
                        yield StreamingData(
                            data=ToolInputDeltaPart(
                                toolCallId=draft_tool_calls[draft_tool_calls_index][
                                    "id"
                                ],
                                inputTextDelta=arguments,
                            )
                        ).dump()

            elif isinstance(chunk, AIMessage) and bool(chunk.usage_metadata):
                if is_text_started:
                    yield StreamingData(data=TextEndPart(id=message_id)).dump()
                    is_text_started = False

                usage_metadata = chunk.usage_metadata
                input_tokens = usage_metadata.get("input_tokens", 0)
                output_tokens = usage_metadata.get("output_tokens", 0)
                total_tokens = usage_metadata.get("total_tokens", 0)

                finish_delta = {
                    "finishReason": "tool-calls"
                    if len(draft_tool_calls) > 0
                    else "stop",
                    "usage": {
                        "promptTokens": input_tokens,
                        "completionTokens": output_tokens,
                        "totalTokens": total_tokens,
                    },
                }

                yield StreamingData(
                    data=DataPart(type="data-usage", data=finish_delta)
                ).dump()
                yield StreamingData.finish().dump()

            else:
                content = chunk.text()

                if not content:
                    continue

                if not is_text_started:
                    yield StreamingData(data=TextStartPart(id=message_id)).dump()
                    is_text_started = True

                yield StreamingData(
                    data=TextDeltaPart(id=message_id, delta=content)
                ).dump()

        if is_text_started:
            yield StreamingData(data=TextEndPart(id=message_id)).dump()
            is_text_started = False

        yield StreamingData.terminate()


class Request(BaseModel):
    id: str
    messages: List[ClientMessage]
    trigger: str


@app.post("/api/chat")
async def handle_chat_data(request: Request, protocol: str = Query("data")):
    messages = request.messages
    converted_messages = convert_to_messages(messages)

    response = StreamingResponse(stream_text(converted_messages, protocol))
    response.headers["x-vercel-ai-ui-message-stream"] = "v1"
    return response


if __name__ == "__main__":
    messages = [
        {
            "role": "user",
            "content": "What is the weather in Tokyo?",
        },
    ]

    def main():
        for chunk in stream_text(messages):
            print(chunk, end="\n")

    main()
