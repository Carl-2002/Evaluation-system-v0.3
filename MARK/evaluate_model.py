import os
import re
import time
from openai import OpenAI
from dotenv import load_dotenv

def chat(query, reference, answer, dropdown, tishici):
    load_dotenv()
    api_key = os.getenv(dropdown+'_KEY')
    base_url = os.getenv(dropdown+'_URL')
    model_name = os.getenv(dropdown+'_NAME')

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    if reference is not None:
        reference_text = f"你的参考提示:{reference}"
    else:
        reference_text = "你没有参考提示。"
    
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
        {"role": "system", "content": tishici},
        {"role": "user", "content": query},
        {"role": "user", "content": reference_text},
        ],
        temperature=0.6,
        stream=False,
    )
    time.sleep(1)
    
    result = completion.choices[0].message.content
    reasoning = getattr(completion.choices[0].message, "reasoning_content", None)

    pattern = r'<think>(.*?)</think>'
    match = re.search(pattern, result, re.DOTALL)

    if match:
        result = re.split(r'</think>\s*', result, maxsplit=1, flags=re.DOTALL)[1]
        reasoning_content = match.group(1).strip()
    elif reasoning:
        reasoning_content = reasoning
    else:
        reasoning_content = None

    score, reason, stop = extract_score_and_reason(result)
    return score, reason, stop, reasoning_content

def extract_score_and_reason(response):
    # 找到第一个阿拉伯数字
    score_match = re.search(r'\d+', response, re.DOTALL)
    if score_match:
        score = int(score_match.group())
        stop = 0
    else:
        score = -9999
        stop = 1
    
    # 找到结构 ":" 或 "：" 并提取其后面的内容直到字符串结束
    reason_match = re.search(r'[：:]\s*(.*)', response, re.DOTALL)
    if reason_match:
        reason = reason_match.group(1)
        stop = 0
    else:
        reason = "-9999"
        stop = 1
    
    return score, reason, stop
