# Welcome to the Large Language Model Testing System (v0.4)!

**2025.03.12**

This system can call your large language model to automatically answer questions and evaluate the responses.

## Usage Instructions

First, you need to open the .env environment file to fill in your large model API, and in the config.txt file, enter the same characters as those before the "_" symbol in the .env file on each line for the program to call.

This project uses the Flask framework, and you can enable the web page by running the 1.py file. The libraries required for the project are listed in requirements.txt, and the specific version of Python is not very important.

The system supports single-turn model dialogues on the page, as well as three types of tests: multiple-choice questions, written questions, and translation questions. It uses Excel files for reading and writing data, and the template for the files can be found at the bottom of the web page. Please fill in the content strictly according to the template to avoid unforeseen errors. Thank you!

The system distinguishes files and their results by filename: "_t" for written question results, "_c" for multiple-choice question results, "_f" for translation question results, "_r" for evaluation results, and "_a" for answer results. The files you upload will be saved in "Uploaded Files" (it is recommended that you rename the files to exclude the aforementioned characters).
# 欢迎来到大语言模型测试系统(v0.4)！

**2025.03.12**

此系统能够调用您的大语言模型自动化回答问题并对回答作出评判。
  
## 使用须知

首先，您需要打开.env环境文件填写您的大模型api，并且在config.txt的每行中填写与.env文件“_”符号前相同的字符，以便程序调用。

本项目使用Flask框架，您可以通过运行1.py文件启用网页。项目所需的库在requirements.txt中，python版本并不十分重要。

该系统支持页面单轮模型对话，以及选择题、文字题与翻译题三种种形式的测试，使用Excel文件读写数据，文件的模板在网页页面下方可见。请您严格按照模板填写内容，避免出现不可预料的错误，谢谢！

该系统以文件名区分文件与文件结果，"_t"：文字题结果，"_c"：选择题结果，"_f"：翻译题结果，"_r"：评测结果，"_a"：回答结果。您上传的文件将保存在“上传文件”中(推荐您修改文件名使它们不含前述这些字符)。
