import json
from typing import Any, List

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from langchain_aws import ChatBedrock
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from pydantic import BaseModel

from .utils.prompt import ClientMessage, convert_to_openai_messages
from .utils.tools import get_current_weather

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
    stream = client_with_tools.stream(
        input=messages[-1]["content"],
    )

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

        for chunk in stream:
            if not isinstance(chunk, BaseMessage):
                continue

            stop_reason = chunk.response_metadata.get("stop_reason")

            if stop_reason == "end_turn":
                continue

            elif stop_reason == "tool_use":
                for tool_call in draft_tool_calls:
                    yield '9:{{"toolCallId":"{id}","toolName":"{name}","args":{args}}}\n'.format(
                        id=tool_call["id"],
                        name=tool_call["name"],
                        args=tool_call["arguments"],
                    )

                for tool_call in draft_tool_calls:
                    tool_result = get_current_weather.invoke(
                        input=json.loads(tool_call["arguments"])
                    )

                    yield 'a:{{"toolCallId":"{id}","toolName":"{name}","args":{args},"result":{result}}}\n'.format(
                        id=tool_call["id"],
                        name=tool_call["name"],
                        args=tool_call["arguments"],
                        result=json.dumps(tool_result),
                    )

            elif isinstance(chunk, AIMessageChunk) and bool(chunk.tool_call_chunks):
                for tool_call in chunk.tool_call_chunks:
                    id = tool_call.get("id")
                    name = tool_call.get("name")
                    arguments = tool_call.get("args")

                    if id is not None:
                        draft_tool_calls_index += 1
                        draft_tool_calls.append(
                            {"id": id, "name": name, "arguments": ""}
                        )
                    else:
                        draft_tool_calls[draft_tool_calls_index]["arguments"] += (
                            arguments
                        )

            elif isinstance(chunk, AIMessage) and bool(chunk.usage_metadata):
                usage_metadata = chunk.usage_metadata
                input_tokens = usage_metadata.get("input_tokens", 0)
                output_tokens = usage_metadata.get("output_tokens", 0)
                total_tokens = usage_metadata.get("total_tokens", 0)

                yield 'd:{{"finishReason":"{reason}","usage":{{"promptTokens":{prompt},"completionTokens":{completion},"totalTokens":{total}}}}}\n'.format(
                    reason="tool-calls" if len(draft_tool_calls) > 0 else "stop",
                    prompt=input_tokens,
                    completion=output_tokens,
                    total=total_tokens,
                )

            else:
                content = chunk.text()

                if not content:
                    continue

                yield "0:{text}\n".format(text=content)


class Request(BaseModel):
    id: str
    messages: List[ClientMessage]
    trigger: str


@app.post("/api/chat")
async def handle_chat_data(request: Request, protocol: str = Query("data")):
    messages = request.messages
    openai_messages = convert_to_openai_messages(messages)

    response = StreamingResponse(stream_text(openai_messages, protocol))
    response.headers["x-vercel-ai-data-stream"] = "v1"
    return response


if __name__ == "__main__":
    messages = [
        ClientMessage(
            role="user",
            content="What is the weather in Tokyo?",
        ),
    ]

    def main():
        for chunk in stream_text(messages):
            print(chunk, end="\n")

    main()
