from dotenv import load_dotenv
import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()
api_key = os.getenv("API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

client = ChatNVIDIA(
  model="mistralai/mistral-large-4-1t-a52b",
  api_key=api_key,
  temperature=0.5,
  top_p=1,
  max_completion_tokens=4096,
  timeout = 240
)

model = ChatGoogleGenerativeAI(
    model = "gemini-3.6-flash",
    google_api_key = google_api_key,
    temperature=0.3,
    top_p=0.95,
    max_output_tokens=4096,
    timeout=120,
    max_retries=2,
)

# invoke_options = {
#   "frequency_penalty": 0,
#   "presence_penalty": 0,
#   "seed": None,
#   "stop": None,
#   "tool_choice": "auto",
#   "reasoning_effort": "medium",
# }


# lc_messages = [
#   {
#     "role": "user",
#     "content": [
#       {
#         "type": "text",
#         "text": "Hi, which is greater 2 or 3",
#       },
#     ],
#   },
# ]

# response = client.invoke(lc_messages, **invoke_options)
# if response.additional_kwargs and "reasoning_content" in response.additional_kwargs:
#   print(response.additional_kwargs["reasoning_content"])
# print(response.content)
# if response.tool_calls:
#   print(response.tool_calls)