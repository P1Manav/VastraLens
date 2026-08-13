import sys
sys.path.append('d:/Projects/TEMP/TailorTalk')
from agent import get_agent
from dotenv import load_dotenv
load_dotenv()
agent = get_agent()
query = "I uploaded an image. Please use your search tool to find similar sarees. Pass the exact string 'current_upload' as the argument to the tool."
response_payload = agent.invoke({"messages": [("user", query)]})
for m in response_payload["messages"]:
    print(m.type, m.content)
    if hasattr(m, "tool_calls"):
        print("Tool calls:", m.tool_calls)
