import os
import sqlite3
import json
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from openai.types.chat import ChatCompletionMessageParam

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

DB_PATH = "shop.db"

class SQLOutput(BaseModel):
    sql: str
    explanation: str

def get_schema(db_path: str):
    # 读取数据库所有表的结构，拼成文本
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    schema_parts = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        cols = ",".join(f"{c[1]}{c[2]}" for c in columns)
        schema_parts.append(f"表{table}: {cols}")
    conn.close()
    return "\n".join(schema_parts)

def generate_sql(question: str, schema: str) -> SQLOutput:
    # 调用模型，把问题翻译成 SQL
    prompt = f"""你是一个 SQL 专家。根据以下数据库结构，将用户的问题转换为 SQL 查询。
    数据库表结构：
    {schema}
    
    用户问题：{question}
    
    只输出 JSON，格式为：
    {{"sql": "你的 SQL 语句"， "explanation": "简要说明"}}
    """

    messages: list[ChatCompletionMessageParam] = [
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=messages,
        response_format={"type": "json_object"}
    )
    raw = response.choices[0].message.content
    return SQLOutput(**json.loads(raw))

def execute_sql(sql: str, db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        columns = [dosc[0] for dosc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return columns, rows
    except Exception as e:
        return [], [("SQL 执行错误", str(e))]
    finally:
        conn.close()

if __name__ == "__main__":
    schema = get_schema(DB_PATH)
    question = input("请输入你的问题：")
    result = generate_sql(question, schema)
    print(f"\n生成的SQL: {result.sql}")
    print(f"说明: {result.explanation}\n")

    columns, rows = execute_sql(result.sql, DB_PATH)
    print(f"列: {columns}")
    for row in rows:
        print(row)