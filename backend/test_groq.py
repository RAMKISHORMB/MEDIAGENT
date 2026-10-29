
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing from backend/.env")

client = Groq(
    api_key=api_key,
    timeout=30.0,
    max_retries=1,
)

print("Testing Groq text completion...")

try:
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: Groq connection works.",
            }
        ],
        max_completion_tokens=300,
    )

    print("Text test: SUCCESS")
    print("Finish reason:", response.choices[0].finish_reason)
    print("Response:", response.choices[0].message.content)

except Exception as error:
    print("Text test: FAILED")
    print("Error type:", type(error).__name__)
    print("Error:", str(error)[:500])


print("\nTesting Groq tool calling...")

try:
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": "Call the ping tool with message='hello'.",
            }
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "ping",
                    "description": "Return a simple diagnostic response.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"}
                        },
                        "required": ["message"],
                        "additionalProperties": False,
                    },
                },
            }
        ],
        tool_choice="required",
        max_completion_tokens=500,
    )

    choice = response.choices[0]
    print("Tool test finish reason:", choice.finish_reason)

    if choice.message.tool_calls:
        for call in choice.message.tool_calls:
            print("Tool called:", call.function.name)
            print("Arguments:", call.function.arguments)
        print("Tool-calling test: SUCCESS")
    else:
        print("Tool-calling test: NO TOOL CALL RETURNED")
        print("Response:", choice.message.content)

except Exception as error:
    print("Tool-calling test: FAILED")
    print("Error type:", type(error).__name__)
    print("Error:", str(error)[:500])