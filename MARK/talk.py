import os
import re
import time
from dotenv import load_dotenv
from openai import OpenAI

def chat(query, reference, dropdown, conversation_history): # 对话
    load_dotenv()
    api_key = os.getenv(dropdown + '_KEY')
    base_url = os.getenv(dropdown + '_URL')
    model_name = os.getenv(dropdown + '_NAME')

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    # 初始化对话历史
    if conversation_history is None:
        conversation_history = []

    # 添加用户消息到对话历史
    conversation_history.append({"role": "user", "content": query})

    # 构建消息列表
    messages = [
        {"role": "system", "content": reference},
    ] + conversation_history

    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.6,
        stream=False,
    )
    time.sleep(1)
    
    result = completion.choices[0].message.content
    
    reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
    print(result)
    
    # 添加助手消息到对话历史
    conversation_history.append({"role": "assistant", "content": result})

    pattern = r'<think>(.*?)</think>'
    match = re.search(pattern, result, re.DOTALL)
    if match:
        return re.split(r'</think>\s*', result, maxsplit=1, flags=re.DOTALL)[1], match.group(1).strip(), conversation_history
    else:
        print(reasoning)
        return result, reasoning, conversation_history