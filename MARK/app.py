import os
import sys
current_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_directory)

import re
import time
import random
import openpyxl
import pandas as pd
from flask import Flask, render_template, request, send_file, jsonify
from flask_socketio import SocketIO, emit

import answer_text
import answer_choose
import evaluate_text
import evaluate_choose
import talk

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

BASE_FOLDER = 'storage'
MOBAN_FOLDER = os.path.join(BASE_FOLDER, 'moban')
UPLOAD_FOLDER = os.path.join(BASE_FOLDER, 'uploads')
ANSWER_FOLDER = os.path.join(BASE_FOLDER, 'answers')
EVALUATION_FOLDER = os.path.join(BASE_FOLDER, 'evaluations')
TISHI_FOLDER = os.path.join(BASE_FOLDER, 'tishi')

os.makedirs(MOBAN_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ANSWER_FOLDER, exist_ok=True)
os.makedirs(EVALUATION_FOLDER, exist_ok=True)
os.makedirs(TISHI_FOLDER, exist_ok=True)

progress_1 = {}
progress_2 = {}

def get_folder_files(folder):
    files_info = []
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        upload_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
        files_info.append({
            'name': filename,
            'size': round(os.path.getsize(file_path) / 1024, 2),
            'uploadTime': upload_time
        })
    return files_info

def get_tishi_file(tishi_filename, socketio):
    tishi_file_path = os.path.join(TISHI_FOLDER, tishi_filename)
    with open(tishi_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    pattern = r'@@@(.*?)@@@'
    matches = re.findall(pattern, content, re.DOTALL)
        
    if len(matches) != 0:
        print(matches)
        return matches
    else:
        error_message = f"提示词格式不正确"
        raise ValueError(error_message)  # 抛出异常以停止程序

def check_keys_match(result_dict, dropdown2, socketio):
    keys = set(result_dict.keys())
    dropdown_set = set(dropdown2)
    if not dropdown_set.issubset(keys):
        error_message = f"提示词与模型无法对应"
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

@app.route('/drawing')
def drawing():
    return render_template('drawing.html')

@app.route('/answer')
def answer():
    return render_template('answer.html')

@app.route('/answer_list')
def answer_list():
    return render_template('answer_list.html', result_files=get_folder_files(ANSWER_FOLDER))

@app.route("/result")
def result():
    return render_template('result.html', result_files=get_folder_files(EVALUATION_FOLDER))

@app.route('/moban')
def moban():
    return jsonify(get_folder_files(MOBAN_FOLDER))

@app.route('/files')
def files():
    return jsonify(get_folder_files(UPLOAD_FOLDER))

@app.route('/tishi_files')
def tishi_files():
    return jsonify(get_folder_files(TISHI_FOLDER))

@app.route('/files_new')
def files_new():
    uploaded_files = get_folder_files(UPLOAD_FOLDER)
    uploaded_files.extend(get_folder_files(ANSWER_FOLDER))
    return jsonify(uploaded_files)

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

@app.route('/download/<filename>')
def download(filename):
    if "_tr" in filename or "_cr" in filename:
        file_path = os.path.join(EVALUATION_FOLDER, filename)
    elif "_ta" in filename or "_ca" in filename:
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
    if "_tr" in filename or "_cr" in filename:
        file_path = os.path.join(EVALUATION_FOLDER, filename)
    elif "_ta" in filename or "_ca" in filename:
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
    dropdown2 = data.get('dropdown2', [])
    dropdown3 = data.get('dropdown3')
    dropdown4 = data.get('dropdown4')  # 新增参数

    if not ((dropdown1 and dropdown3 == 'choose') or (dropdown1 and dropdown3 == 'text_more' and dropdown4 and dropdown2) or (dropdown1 and dropdown3 == 'text_solo' and dropdown4 and dropdown2)):
        error_message = f"请选择所有选项"
        socketio.emit('error_2', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序
    
    base_filename = os.path.splitext(dropdown1)[0]
    file_path = os.path.join(UPLOAD_FOLDER, dropdown1)
    if not os.path.exists(file_path):
        file_path = os.path.join(ANSWER_FOLDER, dropdown1)

    if dropdown3 == "text_solo":
        matches = get_tishi_file("文字评测-唯一.txt", socketio)
        tishici = matches[0].strip()
        
        if dropdown4 == "yes":
            use_general_algorithm = True
            evaluation_suffix = "_tr_d"
        else:
            use_general_algorithm = False
            evaluation_suffix = "_tr"
        
        evaluation_path = os.path.join(EVALUATION_FOLDER, f"{base_filename}_{random.randint(600, 999)}独立{evaluation_suffix}.xlsx")
        evaluate_text.process_file(file_path, dropdown2, socketio, dropdown1, evaluation_path, tishici, use_general_algorithm)
        return jsonify({'message': '评测成功!'}), 202
    elif dropdown3 == "text_more":
        tishi_file_path = os.path.join(TISHI_FOLDER, "文字评测-模型.txt")
        with open(tishi_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        pattern = r'@@@\s*(\w+)\s*\n\*\*\*\n(.*?)\s*@@@'
        matches = re.findall(pattern, content, re.DOTALL)

        result_dict = {key: value.strip() for key, value in matches}
        if not matches:
            error_message = f"提示词格式不正确"
            socketio.emit('error_2', {'message': error_message})
            raise ValueError(error_message)  # 抛出异常以停止程序
            
        check_keys_match(result_dict, dropdown2, socketio)

        if dropdown4 == "yes":
            use_general_algorithm = True
            evaluation_suffix = "_tr_d"
        else:
            use_general_algorithm = False
            evaluation_suffix = "_tr"
        
        evaluation_path = os.path.join(EVALUATION_FOLDER, f"{base_filename}_{random.randint(600, 999)}固定{evaluation_suffix}.xlsx")
        evaluate_text.process_file_solid(file_path, dropdown2, socketio, dropdown1, evaluation_path, result_dict, use_general_algorithm)
        return jsonify({'message': '评测成功!'}), 202
    elif dropdown3 == "choose":
        evaluation_suffix = "_cr"
        evaluation_path = os.path.join(EVALUATION_FOLDER, f"{base_filename}{evaluation_suffix}.xlsx")
        evaluate_choose.evaluate_answers(file_path, socketio, evaluation_path)
        return jsonify({'message': '评测成功!'}), 202
    else:
        return jsonify({'message': '当前评测不支持'}), 400

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.get_json()
    dropdown1 = data.get('dropdown1')
    dropdown2 = data.get('dropdown2', [])  # 修改为列表
    dropdown3 = data.get('dropdown3')

    if not (dropdown1 and dropdown2 and dropdown3):
        error_message = "请选择所有选项"
        socketio.emit('error_1', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序

    if (dropdown1 and len(dropdown2) > 1 and dropdown3 == "choose"):
        error_message = "选择题限选一个模型"
        socketio.emit('error_1', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序
    
    base_filename = os.path.splitext(dropdown1)[0]
    file_path = os.path.join(UPLOAD_FOLDER, dropdown1)
    
    if dropdown3 == "text_free":
        matches = get_tishi_file("文字回答-自由.txt", socketio)

        answer_suffix = "_ta"
        answer_path = os.path.join(ANSWER_FOLDER, f"{base_filename}_{random.randint(100, 599)}自由{answer_suffix}.xlsx")
        answer_text.process_file_free(file_path, dropdown2, socketio, dropdown1, answer_path, matches)
        return jsonify({'message': '测试成功!'}), 202
    if dropdown3 == "text_solid":
        tishi_file_path = os.path.join(TISHI_FOLDER, "文字回答-固定.txt")
        with open(tishi_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        pattern = r'@@@\s*(\w+)\s*\n\*\*\*\n(.*?)\s*@@@'
        matches = re.findall(pattern, content, re.DOTALL)

        result_dict = {key: value.strip() for key, value in matches}
        if not matches:
            error_message = f"提示词格式不正确"
            socketio.emit('error_1', {'message': error_message})
            raise ValueError(error_message)  # 抛出异常以停止程序
        
        check_keys_match(result_dict, dropdown2, socketio)

        answer_suffix = "_ta"
        answer_path = os.path.join(ANSWER_FOLDER, f"{base_filename}_{random.randint(100, 599)}固定{answer_suffix}.xlsx")
        answer_text.process_file_solid(file_path, dropdown2, socketio, dropdown1, answer_path, result_dict)
        return jsonify({'message': '回答成功!'}), 202
    if dropdown3 == "choose":
        matches = get_tishi_file("选择回答-提示.txt", socketio)
        tishici = matches[0].strip()
        
        answer_suffix = "_ca"
        answer_path = os.path.join(ANSWER_FOLDER, f"{base_filename}_{dropdown2[0]}{answer_suffix}.xlsx")
        answer_choose.process_file(file_path, dropdown2[0], socketio, dropdown1, answer_path, tishici)
        return jsonify({'message': '回答成功!'}), 202

@app.route('/get_content')
def get_content():
    # 获取文件名参数
    filename = request.args.get('filename')
    page = int(request.args.get('page', 1))  
    per_page = int(request.args.get('per_page', 40)) 

    file_path = os.path.join(EVALUATION_FOLDER, filename)
    if not os.path.exists(file_path):
        file_path = os.path.join(ANSWER_FOLDER, filename)
        if not os.path.exists(file_path):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if not os.path.exists(file_path):
                return jsonify({'message': '文件不存在'}), 404

    try:
        with pd.ExcelFile(file_path) as excel_data:
            sheets_data = {}
            for sheet_name in excel_data.sheet_names:
                df = excel_data.parse(sheet_name).fillna("无")
                
                # 分页处理
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                paginated_data = df.iloc[start_idx:end_idx]

                original_columns = df.columns.tolist()
                sheets_data[sheet_name] = {
                    "columns": original_columns,
                    "data": [
                        {col: row[col] for col in original_columns}
                        for row in paginated_data.to_dict(orient='records')
                    ],
                    "total_rows": len(df),
                    "current_page": page,
                    "per_page": per_page
                }

        return jsonify({
            'filename': filename,
            'sheets': sheets_data
        })

    except PermissionError:
        return jsonify({'message': '文件被占用，请关闭其他程序后再试'}), 500
    except Exception as e:
        return jsonify({'message': f'读取文件失败: {str(e)}'}), 500

@app.route('/draw_picture')
def draw_picture():
    filename = request.args.get('filename')
    file_path = os.path.join(EVALUATION_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({'message': '文件不存在'}), 404

    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook['指标']
    
    data_list = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        prompt_word = row[0]
        model_name = row[1]
        
        bleu_scores = [row[i] for i in range(2, 6)]
        rouge_scores = [row[i] for i in range(6, 15)]
        
        data_list.append({
            'prompt_word': prompt_word,
            'model_name': model_name,
            'bleu_scores': bleu_scores,
            'rouge_scores': rouge_scores
        })
    
    return jsonify(data_list)

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
    conversation_history = data.get('conversation_history', [])

    result, reasoning, conversation_history = talk.chat(query, reference, dropdown, conversation_history)
    return jsonify({'result': result, 'reasoning': reasoning, 'conversation_history': conversation_history})

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port='8000', debug=True)