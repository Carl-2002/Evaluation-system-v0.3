import os
import time
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

def process_file(file_path, dropdown, socketio, filename, answer_path, matches):  
    df = pd.read_excel(file_path, header=0)  # header=0 表示第一行为列名

    if '选项A' in df.columns or '模型答案' in df.columns or '模型答案(文字题)' in df.columns or '分数' in df.columns or '理由' in df.columns or '问题' in df.columns:
        error_message = f"此为提示词测试，请选择对应文件。"
        socketio.emit('error', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序
    
    if '问题(提示词测试)' not in df.columns or '参考' not in df.columns:
        error_message = f"文件格式不正确，缺少必填列。"
        socketio.emit('error', {'message': error_message})
        raise ValueError(error_message)

    print(dropdown)
    total_questions = len(matches) * len(df)
    t = 0
    
    for i, match in enumerate(matches, start=1):
        print(f"Match {i}: {match.strip()}")
        df['提示词{}'.format(i)] = None
        
        for index, row in df.iterrows():
            if pd.notna(row['问题(提示词测试)']):  
                if pd.notna(row['参考']):
                    reference = row['参考']
                else:
                    reference = None
                
                question = row['问题(提示词测试)']
                time.sleep(1)
                response = chat(question, reference, dropdown, match.strip())
                print("")
                print(response)
                df['提示词{}'.format(i)] = df['提示词{}'.format(i)].astype(str)
                df.at[index, '提示词{}'.format(i)] = str(response)
                
                t = t + 1
                progress = t / total_questions * 100
                socketio.emit('progress', {'filename': filename, 'progress': progress})
            else:
                error_message = f"文件格式: 第 {index + 1} 行数据不正确。"
                socketio.emit('error', {'message': error_message})
                raise ValueError(error_message)  # 抛出异常以停止程序

    df.to_excel(answer_path, sheet_name='数据', index=False)
    socketio.emit('status', {'message': '测试成功!'})

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
   
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": tishici},
            {"role": "user", "content": query },
            {"role": "user", "content": reference_text},
        ],
        temperature=0.3,
        stream=False,
    )
    time.sleep(1)
    
    result = completion.choices[0].message.content
    
    reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
    
    if reasoning:
        return reasoning + result
    else:
        return result