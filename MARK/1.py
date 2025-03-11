import re
import os
import time
import pandas as pd
from flask import Flask, render_template, request, send_file, jsonify
from flask_socketio import SocketIO, emit

import text_xsl
import text_choose
import ask_xsl
import ask_choose
import jiaoliu

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

MOBAN_FOLDER = 'moban'
UPLOAD_FOLDER = 'uploads'
ANSWER_FOLDER = 'answers'
EVALUATION_FOLDER = 'evaluations'
TISHI_FOLDER = 'tishi'

os.makedirs(MOBAN_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ANSWER_FOLDER, exist_ok=True)
os.makedirs(EVALUATION_FOLDER, exist_ok=True)
os.makedirs(TISHI_FOLDER, exist_ok=True)

progress = {}

def get_tishi_file(tishi_filename, socketio):
    tishi_file_path = os.path.join(TISHI_FOLDER, tishi_filename)
    with open(tishi_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        pattern = r'@@@(.*?)@@@'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            tishici = match.group(1).strip()
            print(tishici)
            return tishici
        else:
            error_message = f"提示词格式不正确"
            socketio.emit('error', {'message': error_message})
            raise ValueError(error_message)  # 抛出异常以停止程序

@app.route('/get_models')
def get_models():
    with open('config.txt', 'r') as file:
        box = [line.strip() for line in file]
    return jsonify(box)

@app.route("/")
def hello_world():
    return render_template('index.html')

@app.route("/duihua")
def duihua():
    return render_template('duihua.html')

@app.route("/tishi")
def tishi():
    return render_template('tishi.html')

@app.route("/file")
def file_page():
    return render_template('file.html')

@app.route("/evaluation")
def evaluation():
    return render_template('evaluation.html')

@app.route('/show')
def show():
    return render_template('show.html')

@app.route('/show_choose')
def show_choose():
    return render_template('show_choose.html')

@app.route('/ask_text_1')
def ask_text_1():
    return render_template('ask_text_1.html')

@app.route('/ask_choose_1')
def ask_choose_1():
    return render_template('ask_choose_1.html')

@app.route('/answer')
def answer():
    return render_template('answer.html')

@app.route('/answer_list')
def answer_list():
    result_files = []
    for filename in os.listdir(ANSWER_FOLDER):
        file_path = os.path.join(ANSWER_FOLDER, filename)
        upload_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
        result_files.append({
            'name': filename,
            'size': round(os.path.getsize(file_path) / 1024, 2),
            'uploadTime': upload_time
        })
    return render_template('answer_list.html', result_files=result_files)

@app.route('/moban')
def moban():
    uploaded_files = []
    for filename in os.listdir(MOBAN_FOLDER):
        file_path = os.path.join(MOBAN_FOLDER, filename)
        upload_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
        uploaded_files.append({
            'name': filename,
            'size': round(os.path.getsize(file_path) / 1024, 2),
            'uploadTime': upload_time
        })
    return jsonify(uploaded_files)

@app.route("/result")
def result():
    result_files = []
    for filename in os.listdir(EVALUATION_FOLDER):
        file_path = os.path.join(EVALUATION_FOLDER, filename)
        upload_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
        result_files.append({
            'name': filename,
            'size': round(os.path.getsize(file_path) / 1024, 2),
            'uploadTime': upload_time
        })
    return render_template('result.html', result_files=result_files)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'message': '没有文件上传'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': '没有选择文件'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    upload_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    file_info = {
        'name': file.filename,
        'size': round(os.path.getsize(file_path) / 1024, 2),
        'uploadTime': upload_time
    }
    return jsonify({'message': '文件上传成功', 'fileInfo': file_info})

@app.route('/files')
def files():
    uploaded_files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        upload_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
        uploaded_files.append({
            'name': filename,
            'size': round(os.path.getsize(file_path) / 1024, 2),
            'uploadTime': upload_time
        })
    return jsonify(uploaded_files)

@app.route('/files_new')
def files_new():
    uploaded_files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        upload_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
        uploaded_files.append({
            'name': filename,
            'size': round(os.path.getsize(file_path) / 1024, 2),
            'uploadTime': upload_time
        })
    for filename in os.listdir(ANSWER_FOLDER):
        file_path = os.path.join(ANSWER_FOLDER, filename)
        upload_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
        uploaded_files.append({
            'name': filename,
            'size': round(os.path.getsize(file_path) / 1024, 2),
            'uploadTime': upload_time
        })
    return jsonify(uploaded_files)

@app.route('/download/<filename>')
def download(filename):
    if "_tr" in filename or "_cr" in filename or "_fr" in filename:
        file_path = os.path.join(EVALUATION_FOLDER, filename)
    elif "_ta" in filename or "_ca" in filename or "_fa" in filename:
        file_path = os.path.join(ANSWER_FOLDER, filename)
    elif "_模板" in filename:
        file_path = os.path.join(MOBAN_FOLDER, filename)
    else:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'message': '文件不存在'}), 404

    return send_file(file_path, as_attachment=True)

@app.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    if "_tr" in filename or "_cr" in filename or "_fr" in filename:
        file_path = os.path.join(EVALUATION_FOLDER, filename)
    elif "_ta" in filename or "_ca" in filename or "_fa" in filename:
        file_path = os.path.join(ANSWER_FOLDER, filename)
    else:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'message': '文件不存在'}), 404

    os.remove(file_path)
    return jsonify({'message': '文件删除成功'})

@app.route('/submit_evaluation', methods=['POST'])
def submit_evaluation():
    data = request.get_json()
    dropdown1 = data.get('dropdown1')
    dropdown2 = data.get('dropdown2')
    dropdown3 = data.get('dropdown3')
    dropdown4 = data.get('dropdown4')  # 新增参数

    if not (dropdown1 and dropdown3 == 'choose') and not (dropdown1 and dropdown3 == 'fanyi' and dropdown4 and dropdown2):
        error_message = f"请选择所有选项"
        socketio.emit('error', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序

    base_filename = os.path.splitext(dropdown1)[0]
    
    file_path = os.path.join(UPLOAD_FOLDER, dropdown1)
    if not os.path.exists(file_path):
        file_path = os.path.join(ANSWER_FOLDER, dropdown1)

    if dropdown3 == "text":
        tishici = get_tishi_file("文字评测-提示.txt", socketio)
        
        evaluation_suffix = "_tr"
        evaluation_path = os.path.join(EVALUATION_FOLDER, f"{base_filename}_{dropdown2}{evaluation_suffix}.xlsx")
        if dropdown4 == "yes":
            text_xsl.process_file(file_path, dropdown2, socketio, dropdown1, evaluation_path, tishici, use_general_algorithm=True)
            return jsonify({'message': '评测成功!'}), 202
        else:
            text_xsl.process_file(file_path, dropdown2, socketio, dropdown1, evaluation_path, tishici, use_general_algorithm=False)
            return jsonify({'message': '评测成功!'}), 202
    elif dropdown3 == "fanyi":
        tishici = get_tishi_file("翻译评测-提示.txt", socketio)
        
        evaluation_suffix = "_fr"
        evaluation_path = os.path.join(EVALUATION_FOLDER, f"{base_filename}_{dropdown2}{evaluation_suffix}.xlsx")
        if dropdown4 == "yes":
            text_xsl.process_file(file_path, dropdown2, socketio, dropdown1, evaluation_path, tishici, use_general_algorithm=True)
            return jsonify({'message': '评测成功!'}), 202
        else:
            text_xsl.process_file(file_path, dropdown2, socketio, dropdown1, evaluation_path, tishici, use_general_algorithm=False)
            return jsonify({'message': '评测成功!'}), 202
    elif dropdown3 == "choose":
        evaluation_suffix = "_cr"
        evaluation_path = os.path.join(EVALUATION_FOLDER, f"{base_filename}{evaluation_suffix}.xlsx")
        text_choose.evaluate_answers(file_path, socketio, evaluation_path)
        return jsonify({'message': '评测成功!'}), 202
    else:
        return jsonify({'message': '当前评测不支持'}), 400

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.get_json()
    dropdown1 = data.get('dropdown1')
    dropdown2 = data.get('dropdown2')
    dropdown3 = data.get('dropdown3')

    if not dropdown1 or not dropdown2 or not dropdown3:
        error_message = f"请选择所有选项"
        socketio.emit('error', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序

    base_filename = os.path.splitext(dropdown1)[0]
    file_path = os.path.join(UPLOAD_FOLDER, dropdown1)
    
    if dropdown3 == "text":
        tishici = get_tishi_file("文字回答-提示.txt", socketio)

        answer_suffix = "_ta"
        answer_path = os.path.join(ANSWER_FOLDER, f"{base_filename}_{dropdown2}{answer_suffix}.xlsx")
        ask_xsl.process_file(file_path, dropdown2, socketio, dropdown1, answer_path, tishici)
        return jsonify({'message': '回答成功!'}), 202
    if dropdown3 == "fanyi":
        tishici = get_tishi_file("翻译回答-提示.txt", socketio)

        answer_suffix = "_fa"
        answer_path = os.path.join(ANSWER_FOLDER, f"{base_filename}_{dropdown2}{answer_suffix}.xlsx")
        ask_xsl.process_file(file_path, dropdown2, socketio, dropdown1, answer_path, tishici)
        return jsonify({'message': '回答成功!'}), 202
    if dropdown3 == "choose":
        tishici = get_tishi_file("选择回答-提示.txt", socketio)
        
        answer_suffix = "_ca"
        answer_path = os.path.join(ANSWER_FOLDER, f"{base_filename}_{dropdown2}{answer_suffix}.xlsx")
        ask_choose.process_file(file_path, dropdown2, socketio, dropdown1, answer_path, tishici)
        return jsonify({'message': '回答成功!'}), 202

@app.route('/get_content')
def get_content():
    filename = request.args.get('filename')
    file_path = os.path.join(EVALUATION_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({'message': '文件不存在'}), 404

    try:
        df = pd.read_excel(file_path, sheet_name='数据', header=0)  # header=0 表示第一行为列名
        
        data = df.to_dict(orient='records')
        
        newdata = []
        t = 0
        for item in data:
            new_item = {
                '问题': item['问题'],
                '模型答案(文字题)': item['模型答案(文字题)'],
                '标准答案(文字题)': item['标准答案(文字题)'] if pd.notna(item['标准答案(文字题)']) else '无',
                '分数': item['分数'] if pd.notna(item['分数']) else '无',
                '原因': item['原因'] if pd.notna(item['原因']) else '无'
            }
            newdata.append(new_item)
            t = t + 1
            if t == 20:
                break
            
        df2 = pd.read_excel(file_path, sheet_name='统计')
        stats = {
            'total_questions':  int(df2.iloc[0, 0]),  # 转换为 int
            'average': float(df2.iloc[0, 1]),
            'medium': float(df2.iloc[0, 2]),
            'standard_deviation': float(df2.iloc[0, 3]),
         }        

        if df2.iloc[2, 0] == '不计算通用模型参数':
            draw_charts = 0
            rouge_data = None
            bleu_score = None
        else:   
            draw_charts = 1
            bleu_score = [df2.iloc[3, 0], df2.iloc[3, 1], df2.iloc[3, 2], df2.iloc[3, 3]]
        
            df3 = pd.read_excel(file_path, sheet_name='rouge')
        
            rouge_data = {
                'rouge-1': {'r': df3.iloc[0, 1], 'p': df3.iloc[0, 2], 'f': df3.iloc[0, 3]},
                'rouge-2': {'r': df3.iloc[1, 1], 'p': df3.iloc[1, 2], 'f': df3.iloc[1, 3]},
                'rouge-l': {'r': df3.iloc[2, 1], 'p': df3.iloc[2, 2], 'f': df3.iloc[2, 3]},
            }
            print(rouge_data)
            print(bleu_score)
        
        return jsonify({
            'data': newdata,
            'stats': stats,
            'rouge': rouge_data,
            'bleu_score': bleu_score,
            'draw_charts': draw_charts  # 添加 draw_charts 参数
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/api/excel-data')
def excel_data():
    filename = request.args.get('filename')
    file_path = os.path.join(EVALUATION_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({'message': '文件不存在'}), 404

    try:
        df = pd.read_excel(file_path, sheet_name='数据', header=0)
        data = df.to_dict(orient='records')

        newdata = []
        t = 0
        for item in data:
            new_item = {
                '问题': item['问题'] if pd.notna(item['问题']) else '无',
                '选项A': item['选项A'] if pd.notna(item['选项A']) else '无',
                '选项B': item['选项B'] if pd.notna(item['选项B']) else '无',
                '选项C': item['选项C'] if pd.notna(item['选项C']) else '无',
                '选项D': item['选项D'] if pd.notna(item['选项D']) else '无',
                '模型答案': item['模型答案'],
                '标准答案': item['标准答案'],
                '结果': item['结果'],
            }
            newdata.append(new_item)
            t = t + 1
            if t == 20:
                break

        df2 = pd.read_excel(file_path, sheet_name='统计')
        statss = {
            'total_questions': int(df2.iloc[0, 0]),
            'correct_count': int(df2.iloc[0, 1]),
            'incorrect_count': int(df2.iloc[0, 2]),
            'accuracy': float(df2.iloc[0, 3])
        }
        print(statss)
        
        return jsonify({
            'data': newdata,
            'statss': statss
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/api/excel-answer')
def excel_answer():
    filename = request.args.get('filename')
    file_path = os.path.join(ANSWER_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({'message': '文件不存在'}), 404

    try:
        df = pd.read_excel(file_path, header=0)
        data = df.to_dict(orient='records')

        newdata = []
        t = 0
        for item in data:
            new_item = {
                '问题': item['问题'],
                '选项A': item['选项A'],
                '选项B': item['选项B'],
                '选项C': item['选项C'],
                '选项D': item['选项D'],
                '模型答案': item['模型答案'] if pd.notna(item['模型答案']) else '无',
                '理由': item['理由'] if pd.notna(item['理由']) else '无',
            }
            newdata.append(new_item)
            t = t + 1
            if t == 20:
                break
        
        return jsonify({
            'data': newdata,
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/get_content_ask')
def get_content_ask():
    filename = request.args.get('filename')
    file_path = os.path.join(ANSWER_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({'message': '文件不存在'}), 404

    try:
        df = pd.read_excel(file_path, header=0)  # header=0 表示第一行为列名
        data = df.to_dict(orient='records')
        
        newdata = []
        t = 0
        for item in data:
            new_item = {
                '问题': item['问题'],
                '模型答案(文字题)': item['模型答案(文字题)'] if pd.notna(item['模型答案(文字题)']) else '无',
            }
            newdata.append(new_item)
            t = t + 1
            if t == 20:
                break
        
        return jsonify({
            'data': newdata,
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/tishi_files')
def tishi_files():
    uploaded_files = []
    for filename in os.listdir(TISHI_FOLDER):
        if filename.endswith('.txt'):
            file_path = os.path.join(TISHI_FOLDER, filename)
            upload_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
            uploaded_files.append({
                'name': filename,
                'size': round(os.path.getsize(file_path) / 1024, 2),
                'uploadTime': upload_time
            })
    return jsonify(uploaded_files)

@app.route('/read_tishi_file', methods=['GET'])
def read_tishi_file():
    filename = request.args.get('filename')
    file_path = os.path.join(TISHI_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({'message': '文件不存在'}), 404

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    return jsonify({'content': content})

@app.route('/save_tishi_file', methods=['POST'])
def save_tishi_file():
    data = request.get_json()
    filename = data.get('filename')
    content = data.get('content')

    if not filename or not content:
        return jsonify({'message': '缺少参数'}), 400

    file_path = os.path.join(TISHI_FOLDER, filename)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

    return jsonify({'message': '文件保存成功'})

@app.route('/chat', methods=['POST'])
def handle_chat():
    data = request.get_json()
    query = data.get('query')
    reference = data.get('reference')
    dropdown = data.get('dropdown')

    result, reasoning = jiaoliu.chat(query, reference, dropdown)
    return jsonify({'result': result, 'reasoning': reasoning})

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == "__main__":
    socketio.run(app, debug=True)  # 启用多线程和 SocketIO