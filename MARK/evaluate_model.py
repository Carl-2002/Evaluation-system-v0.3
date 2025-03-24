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
        {"role": "user", "content": f"问题是:{query}\n答案是:{answer}"},
        {"role": "user", "content": reference_text},
        ],
        temperature=0.5,
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
    else:
        reasoning_content = reasoning

    score, reason, stop = extract_score_and_reason(result)
    return score, reason, stop, reasoning_content

def extract_score_and_reason(response):
    match = None
    for match in re.finditer(r'[1-5]', response[::-1]): 
        break  
    
    if match:
        score = int(match.group())  # 获取匹配的数字
        stop = 0
    else:
        score = -9999  # 如果没有匹配到，返回默认值
        stop = 1
    
    return score, response, stop
