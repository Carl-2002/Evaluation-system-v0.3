import os
import re
import time
from dotenv import load_dotenv
from openai import OpenAI

def chat(query, reference, dropdown):
    load_dotenv()
    api_key = os.getenv(dropdown + '_KEY')
    base_url = os.getenv(dropdown + '_URL')
    model_name = os.getenv(dropdown + '_NAME')

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": reference},
            {"role": "user", "content": query}
        ],
        temperature=0.3,
        stream=False,
    )
    time.sleep(1)
    
    result = completion.choices[0].message.content
    
    reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
    print(result)
    
    pattern = r'<think>(.*?)</think>'
    match = re.search(pattern, result, re.DOTALL)
    if match:
        return re.split(r'</think>\s*', result, maxsplit=1, flags=re.DOTALL)[1], match.group(1)
    elif reasoning:
        print(reasoning)
        return result, reasoning
    else:
        return result, "无"