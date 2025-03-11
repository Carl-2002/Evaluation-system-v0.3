import time
import re
from openai import OpenAI
import os
from dotenv import load_dotenv

def choose(query, A, B, C, D, reference, dropdown, tishici):
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
        {"role": "user", "content": reference_text},
        {"role": "user", "content": f"问题是: {query}\n选项A: {A}\n选项B: {B}\n选项C: {C}\n选项D: {D}\n请根据上述标准作答：" }
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
        letter, reason, stop = extract_mark(result)
        return letter, reason, stop, match.group(1)
    elif reasoning:
        print(reasoning)
        letter, reason, stop = extract_mark(result)
        return letter, reason, stop, reasoning
    else:
        letter, reason, stop = extract_mark(result)
        return letter, reason, stop, None
    

def chat(query, reference, dropdown, tishici):
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
            {"role": "user", "content": f"{ciyu1}是: {query}\n请根据上述要求{ciyu2}：" }
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
        return re.split(r'</think>\s*', result, maxsplit=1)[1], match.group(1)
    elif reasoning:
        print(reasoning)
        return result, reasoning
    else:
        return result, None

def extract_mark(response):
    # 找到第一个字母
    letter_match = re.search(r'[A-D]', response)
    if letter_match:
        letter = letter_match.group()
        print(letter)
        stop = 0
    else:
        letter = '-FFFF'
        print("未找到字母")
        stop = 1
    
    # 找到结构 ":" 或 "：" 并提取其后面的内容直到字符串结束
    reason_match = re.search(r'[：:]\s*(.*)', response)
    if reason_match:
        reason = reason_match.group(1)
        print(reason)
        stop = 0
    else:
        reason = "-FFFF"
        print("未找到内容")
        stop = 1
    return letter, reason, stop
