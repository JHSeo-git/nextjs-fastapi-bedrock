from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class BasePart(BaseModel):
    type: str = Field(..., description="The type of the streaming data")


class MessageStartPart(BasePart):
    type: Optional[Literal["start"]] = Field(
        "start", description="The type of the streaming data"
    )
    messageId: str = Field(..., description="The message id of the streaming data")


class TextStartPart(BasePart):
    type: Optional[Literal["text-start"]] = Field(
        "text-start", description="The type of the streaming data"
    )
    id: str = Field(..., description="The id of the streaming data")


class TextDeltaPart(BasePart):
    type: Optional[Literal["text-delta"]] = Field(
        "text-delta", description="The type of the streaming data"
    )
    id: str = Field(..., description="The id of the streaming data")
    delta: str = Field(..., description="The text of the streaming data")


class TextEndPart(BasePart):
    type: Optional[Literal["text-end"]] = Field(
        "text-end", description="The type of the streaming data"
    )
    id: str = Field(..., description="The id of the streaming data")


class ReasoningStartPart(BasePart):
    type: Optional[Literal["reasoning-start"]] = Field(
        "reasoning-start", description="The type of the streaming data"
    )
    id: str = Field(..., description="The id of the streaming data")


class ReasoningDeltaPart(BasePart):
    type: Optional[Literal["reasoning-delta"]] = Field(
        "reasoning-delta", description="The type of the streaming data"
    )
    id: str = Field(..., description="The id of the streaming data")
    delta: str = Field(..., description="The reasoning of the streaming data")


class ReasoningEndPart(BasePart):
    type: Optional[Literal["reasoning-end"]] = Field(
        "reasoning-end", description="The type of the streaming data"
    )
    id: str = Field(..., description="The id of the streaming data")


class SourceUrlPart(BasePart):
    type: Optional[Literal["source-url"]] = Field(
        "source-url", description="The type of the streaming data"
    )
    sourceId: str = Field(..., description="The source id of the streaming data")
    url: str = Field(..., description="The url of the streaming data")


class SourceDocumentPart(BasePart):
    type: Optional[Literal["source-document"]] = Field(
        "source-document", description="The type of the streaming data"
    )
    sourceId: str = Field(..., description="The source id of the streaming data")
    mediaType: str = Field(..., description="The media type of the streaming data")
    title: str = Field(..., description="The title of the streaming data")


class FilePart(BasePart):
    type: Optional[Literal["file"]] = Field(
        "file", description="The type of the streaming data"
    )
    url: str = Field(..., description="The url of the streaming data")
    mediaType: str = Field(..., description="The media type of the streaming data")


class DataPart(BasePart):
    data: Optional[Any] = Field(None, description="The data of the streaming data")


class ErrorPart(BasePart):
    type: Optional[Literal["error"]] = Field(
        "error", description="The type of the streaming data"
    )
    errorText: str = Field(..., description="The error text of the streaming data")


class ToolInputStartPart(BasePart):
    type: Optional[Literal["tool-input-start"]] = Field(
        "tool-input-start", description="The type of the streaming data"
    )
    toolCallId: str = Field(..., description="The tool call id of the streaming data")
    toolName: str = Field(..., description="The tool name of the streaming data")


class ToolInputDeltaPart(BasePart):
    type: Optional[Literal["tool-input-delta"]] = Field(
        "tool-input-delta", description="The type of the streaming data"
    )
    toolCallId: str = Field(..., description="The tool call id of the streaming data")
    inputTextDelta: str = Field(..., description="The delta of the streaming data")


class ToolInputAvailablePart(BasePart):
    type: Optional[Literal["tool-input-available"]] = Field(
        "tool-input-available", description="The type of the streaming data"
    )
    toolCallId: str = Field(..., description="The tool call id of the streaming data")
    toolName: str = Field(..., description="The tool name of the streaming data")
    input: Union[str, dict[str, Any]] = Field(
        ..., description="The input of the streaming data"
    )


class ToolOutputAvailablePart(BasePart):
    type: Optional[Literal["tool-output-available"]] = Field(
        "tool-output-available", description="The type of the streaming data"
    )
    toolCallId: str = Field(..., description="The tool call id of the streaming data")
    output: Union[str, dict[str, Any]] = Field(
        ..., description="The output of the streaming data"
    )


class StartStepPart(BasePart):
    type: Optional[Literal["start-step"]] = Field(
        "start-step", description="The type of the streaming data"
    )


class FinishStepPart(BasePart):
    type: Optional[Literal["finish-step"]] = Field(
        "finish-step", description="The type of the streaming data"
    )


class FinishMessagePart(BasePart):
    type: Optional[Literal["finish"]] = Field(
        "finish", description="The type of the streaming data"
    )


class StreamingData(BaseModel):
    data: Union[
        MessageStartPart,
        TextStartPart,
        TextDeltaPart,
        TextEndPart,
        ReasoningStartPart,
        ReasoningDeltaPart,
        ReasoningEndPart,
        SourceUrlPart,
        SourceDocumentPart,
        FilePart,
        DataPart,
        ErrorPart,
        ToolInputStartPart,
        ToolInputDeltaPart,
        ToolInputAvailablePart,
        ToolOutputAvailablePart,
        StartStepPart,
        FinishStepPart,
        FinishMessagePart,
    ]

    def dump(self):
        return f"data: {self.data.model_dump_json()}\n\n"

    @classmethod
    def start(cls, message_id: str):
        return cls(data=MessageStartPart(messageId=message_id))

    @classmethod
    def finish(cls):
        return cls(data=FinishMessagePart())

    @classmethod
    def terminate(cls):
        return "data: [DONE]\n\n"


if __name__ == "__main__":

    def test():
        data = StreamingData(data=TextStartPart(id="test"))
        print(data.model_dump_json(indent=2))

    test()
