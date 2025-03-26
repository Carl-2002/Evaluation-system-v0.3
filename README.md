# Welcome to the Large Language Model Testing System (v0.6)!

**2025.03.26**

A brand new version is now live! This system uses a large language model to automatically answer questions and evaluate those answers.

## Usage Instructions

First, you need to open the .env environment file to configure your large language model API, and fill in each line of the config.txt file with the same characters as before the "_" symbol in the .env file for the program to function correctly.

This project is based on the Flask framework, and you can start the webpage by simply running the app.py file. The required libraries can be found in the requirements.txt file, and the Python version requirement is not strict.

The system supports multi-turn conversations, prompt debugging, as well as testing multiple-choice questions and written questions, allowing for batch reading and writing of data through Excel files. File templates can be found at the bottom of the webpage, and please make sure to fill them out according to the template to avoid any inadvertent errors. The files and results are distinguished by their filenames, where "_t" represents the written question results, "_c" represents the multiple-choice question results, "_r" represents the evaluation results, "_a" represents the answer results, and "_d" includes drawing results. The files you upload will be stored in "Uploaded Files," and it is recommended to rename the files to avoid using the characters mentioned above.

Before using this system, we recommend that you read the usage instructions at the bottom of the page. If you encounter any issues, we appreciate your understanding! Thank you all for your support!

# 欢迎来到大语言模型测试系统(v0.6)！

**2025.03.26**

全新版本上线！本系统利用大型语言模型自动回答问题，并对答案进行评估。
  
## 使用须知

首先，您需要打开.env环境文件配置您的大语言模型API，并且在config.txt的每行中填写与.env文件“_”符号前相同的字符，以便程序调用。

该项目基于Flask框架，您只需运行app.py文件即可启动网页。所需的库可以在requirements.txt中找到，Python版本要求不严格。

系统支持多轮对话、提示词调试，以及选择题和文字题的测试，通过Excel文件批量读写数据。文件模板可在网页底部找到，请务必按照模板填写，以避免意外错误。文件与结果以文件名区分，其中"_t"代表文字题结果，"_c"代表选择题结果，"_r"代表评测结果，"_a"代表回答结果，"_d"包含画图结果。您上传的文件将保存在“上传文件”中，建议您修改文件名，避免使用上述字符。

在使用本系统前，推荐您阅读页面下方的使用说明。如遇任何问题，敬请谅解！谢谢大家的支持！