import os
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

load_dotenv()  # 自动读取项目根目录下的 .env 文件，把里面的 DEEPSEEK_API_KEY 加载到系统环境中

# Deepseek 的 API 兼容 OpenAI 的接口规范
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# messages 列表里面，每一条信息的字典必须是严格定义的特定格式：
# 1. role 必须是 Literal["system"]（只能用 "system" 这个字符串，不能是随便的字符串）
# 2. content 必须是 str
messages: list[ChatCompletionMessageParam] = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello"}
]

response = client.chat.completions.create(
    model="deepseek-flash",
    messages = messages
)

print(response.choices[0].message.content)