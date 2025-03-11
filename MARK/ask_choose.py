import pandas as pd
import time
from model_ask import choose
from openpyxl import load_workbook

def process_file(file_path, dropdown, socketio, filename, answer_path, tishici):
    df = pd.read_excel(file_path, header=0)  # header=0 表示第一行为列名

    if '模型答案(文字题)' in df.columns or '标准答案(文字题)' in df.columns:
        error_message = f"此为选择题，请选择选择题文件。"
        socketio.emit('error', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序
    
    if '问题' not in df.columns or '选项A' not in df.columns or '选项B' not in df.columns or '选项C' not in df.columns or '选项D' not in df.columns or '参考' not in df.columns or '模型答案' not in df.columns or '标准答案' not in df.columns or '理由' not in df.columns or '结果' not in df.columns:
        error_message = f"文件格式不正确，缺少必填列。"
        socketio.emit('error', {'message': error_message})
        raise ValueError(error_message)

    print(dropdown)
    think_box = []
    
    total_questions = len(df)
    stop_1 = 0
    for index, row in df.iterrows():
        if pd.notna(row['问题']) and pd.notna(row['选项A']) and pd.notna(row['选项B']) and pd.notna(row['选项C']) and pd.notna(row['选项D']) and pd.isna(row['模型答案']) and pd.isna(row['理由']):  
            if pd.notna(row['参考']):
                reference = row['参考']
            else:
                reference = None
            
            question = row['问题']
            A = row['选项A']
            B = row['选项B']
            C = row['选项C']
            D = row['选项D']
            time.sleep(1)
            xuanxiang, liyou, stop, think = choose(question, A, B, C, D, reference, dropdown, tishici)
            print("")
            if stop == 1:
                stop_1 = 1
            df['模型答案'] = df['模型答案'].astype(str)
            df['理由'] = df['理由'].astype(str)
            df.at[index, '模型答案'] = str(xuanxiang)
            df.at[index, '理由'] = str(liyou)
            if think is not None:
                think_box.append({index:think})
            
            # 更新进度
            progress = (index + 1) / total_questions * 100
            socketio.emit('progress', {'filename': filename, 'progress': progress})

        else:
            error_message = f"文件格式: 第 {index + 1} 行数据不正确。"
            socketio.emit('error', {'message': error_message})
            raise ValueError(error_message)  # 抛出异常以停止程序

    with pd.ExcelWriter(answer_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='数据', index=False)
        
        workbook = writer.book
        stats_sheet = workbook['数据']
    
        if len(think_box) > 0:
            stats_sheet['L1'] = '回答think'
            for i in think_box:
                index = list(i.keys())[0]
                think = i[index]
                stats_sheet[f'L{index + 2}'] = think
            think_box.clear()
    
    if stop_1 == 1:  # 如果有停止标志，则发送停止信号
        socketio.emit('status', {'message': '回答中有错误，请检查结果！(-FFFF)'})
    else:
        socketio.emit('status', {'message': '回答成功!'})