import time
import re
from openai import OpenAI
import os
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
    if re.search(r'翻译', tishici): 
        ciyu1 = "原句"
        ciyu2 = "翻译"
    else:
        ciyu1 = "问题"
        ciyu2 = "回答"
    
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
        {"role": "system", "content": tishici},
        {"role": "user", "content": reference_text},
        {"role": "user", "content": f"{ciyu1}是: {query}\n{ciyu2}是: {answer}\n请根据上述标准对这个{ciyu2}评分并阐述理由。"}
        ],
        temperature=0.3,
        stream=False,
    )
    time.sleep(1)
    
    result = completion.choices[0].message.content
    
    reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
    
    result = result.replace('\n', '')
    print(result)
    
    pattern = r'<think>(.*?)</think>'
    match = re.search(pattern, result)
    if match:
        result = re.split(r'</think>\s*', result, maxsplit=1)[1]
        score, reason, stop = extract_score_and_reason(result)
        return score, reason, stop, match.group(1)
    elif reasoning:
        print(reasoning)
        score, reason, stop = extract_score_and_reason(result)
        return score, reason, stop, reasoning
    else:
        score, reason, stop = extract_score_and_reason(result)
        return score, reason, stop, None

def extract_score_and_reason(response):
    # 找到第一个阿拉伯数字
    score_match = re.search(r'\d+', response)
    if score_match:
        score = int(score_match.group())
        print(score)
        stop = 0
    else:
        score = -9999
        print("未找到数字")
        stop = 1
    
    # 找到结构 ":" 或 "：" 并提取其后面的内容直到字符串结束
    reason_match = re.search(r'[：:]\s*(.*)', response)
    if reason_match:
        reason = reason_match.group(1)
        print(reason)
        stop = 0
    else:
        reason = "-9999"
        print("未找到内容")
        stop = 1
    
    return score, reason, stop
