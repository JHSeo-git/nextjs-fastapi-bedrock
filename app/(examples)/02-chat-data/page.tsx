"use client";

import { Card } from "@/app/components";
import { useChat } from "@ai-sdk/react";
import { getToolName, isToolUIPart } from "ai";
import { GeistMono } from "geist/font/mono";
import { useState } from "react";

export default function Page() {
  const [input, setInput] = useState("");
  const { messages, sendMessage, status } = useChat({
    onError: (error) => {
      console.error(error);
    },
  });

  console.log({ messages });

  return (
    <div className="flex flex-col gap-2 pb-14">
      <div className="flex flex-col gap-2 p-4">
        {messages.map((message) => (
          <div key={message.id} className="flex flex-row gap-2">
            <div className="flex-shrink-0 w-24 text-zinc-500">{`${message.role}: `}</div>

            <div className="flex flex-col gap-2">
              <details>
                <summary>{message.id}</summary>
                <pre className="p-2 text-sm border rounded-md w-[600px] overflow-scroll">
                  {JSON.stringify(message, null, 2)}
                </pre>
              </details>
              {message.parts.map((part, index) => {
                if (part.type === "text") {
                  return <div key={index}>{part.text}</div>;
                } else if (isToolUIPart(part)) {
                  return (
                    <div key={index}>
                      <div
                        className={`${GeistMono.className} text-sm p-3 rounded-lg border`}
                      >
                        <strong>function: </strong>
                        {`${getToolName(part)}(${JSON.stringify(
                          part.input,
                          null,
                          2
                        )})`}
                      </div>
                      {Boolean(part.output) && (
                        <div
                          className={`${GeistMono.className} text-sm mt-2 p-3 rounded-lg border`}
                        >
                          <strong>result: </strong>
                          <pre>{JSON.stringify(part.output, null, 2)}</pre>
                        </div>
                      )}
                    </div>
                  );
                } else if (part.type === "data-usage") {
                  return (
                    <div
                      key={index}
                      className={`${GeistMono.className} text-sm p-3 rounded-lg border`}
                    >
                      <strong>usage: </strong>
                      <pre>{JSON.stringify(part.data, null, 2)}</pre>
                    </div>
                  );
                }
              })}
            </div>
          </div>
        ))}
      </div>

      {messages.length === 0 && <Card type="chat-data" />}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage({ text: input });
          setInput("");
        }}
        className="fixed bottom-0 flex flex-col w-full border-t z-10 bg-white"
      >
        <input
          value={input}
          placeholder="What's the weather in San Francisco?"
          onChange={(e) => setInput(e.target.value)}
          className="w-full p-4 bg-transparent outline-none"
          disabled={status !== "ready"}
        />
      </form>
    </div>
  );
}
