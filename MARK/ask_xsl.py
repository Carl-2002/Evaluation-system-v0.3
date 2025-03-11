import pandas as pd
import time
from model_ask import chat
from openpyxl import load_workbook

def process_file(file_path, dropdown, socketio, filename, answer_path, tishici):  
    df = pd.read_excel(file_path, header=0)  # header=0 表示第一行为列名

    if '选项A' in df.columns or '模型答案' in df.columns:
        error_message = f"此为文字题，请选择文字题文件。"
        socketio.emit('error', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序
    
    if '问题' not in df.columns or '模型答案(文字题)' not in df.columns or '参考' not in df.columns or '标准答案(文字题)' not in df.columns or '分数' not in df.columns or '原因' not in df.columns:
        error_message = f"文件格式不正确，缺少必填列。"
        socketio.emit('error', {'message': error_message})
        raise ValueError(error_message)

    print(dropdown)
    think_box = []
    
    total_questions = len(df)
    for index, row in df.iterrows():
        if pd.notna(row['问题']) and pd.isna(row['模型答案(文字题)']):  
            if pd.notna(row['参考']):
                reference = row['参考']
            else:
                reference = None
            
            question = row['问题']
            time.sleep(1)
            response, think= chat(question, reference, dropdown, tishici)
            print("")
            df['模型答案(文字题)'] = df['模型答案(文字题)'].astype(str)
            df.at[index, '模型答案(文字题)'] = str(response)
            if think is not None:
                think_box.append({index:think})
            
            progress = (index + 1) / total_questions * 100
            socketio.emit('progress', {'filename': filename, 'progress': progress})
        else:
            error_message = f"文件格式: 第 {index + 1} 行数据不正确。"
            socketio.emit('error', {'message': error_message})
            raise ValueError(error_message)  # 抛出异常以停止程序
    
    
    with pd.ExcelWriter(answer_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='数据', index=False)
            
        # 获取工作簿和工作表
        workbook = writer.book
        stats_sheet = workbook['数据']
    
        if len(think_box) > 0:
            stats_sheet['L1'] = '回答think'
            for i in think_box:
                index = list(i.keys())[0]
                think = i[index]
                stats_sheet[f'L{index + 2}'] = think
            think_box.clear()
        
    socketio.emit('status', {'message': '回答成功!'})