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
    prompt = f"""
        你是一个 SQL 专家。根据以下数据库结构，将用户的问题转换为 SQL 查询。
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
    """
    :param sql: 大模型返回的 sql 语句
    :param db_path: 数据库
    :return: columns_字段名 rows_行数据
    """
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

def nl2sql_with_retry(question: str, schema: str, db_path: str, max_retries: int = 3):
    last_error = None
    last_sql = None

    for attempt in range(max_retries):
        if attempt == 0:
            result = generate_sql(question, schema)
        else:
            fix_prompt = f"""
                之前生成的 SQL 执行失败，请修正。

                原问题：{question}

                数据库表结构：{schema}

                失败的 SQL：{last_sql}

                错误信息：{last_error}

                请生成修正后的 SQL，只输出 JSON：
                {{"sql": "修正后的 SQL", "explanation": "说明修改了什么"}}
            """

            response = client.chat.completions.create(
                model="deepseek-flash",
                messages=[{"role": "user", "content": fix_prompt}],
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content
            result = SQLOutput(**json.loads(raw))

        columns, rows = execute_sql(result.sql, db_path)

        # 判断是否执行成功：如果第一列是 “SQL 执行错误”，说明失败
        if columns and rows[0] != "SQL执行错误":
            return result, columns, rows

        # 记录失败信息，用于下一次重试
        last_sql = result.sql
        last_error = str(row)

    # 所有重试都失败
    return result, [], [("重试失败", f"已尝试{max_retries}次，最后一次错误：{last_error}")]

if __name__ == "__main__":
    schema = get_schema(DB_PATH)
    question = input("请输入你的问题：")
    result, columns, rows = nl2sql_with_retry(question, schema, DB_PATH)

    print(f"\n生成的SQL: {result.sql}")
    print(f"说明: {result.explanation}\n")
    print(f"列: {columns}")
    for row in rows:
        print(row)