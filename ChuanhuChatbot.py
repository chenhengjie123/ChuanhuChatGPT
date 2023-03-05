import gradio as gr
import openai
import os
import sys
import markdown

import argparse

from markdown.extensions.codehilite import CodeHiliteExtension

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
initial_prompt = "You are a helpful assistant."


if OPENAI_API_KEY == "empty":
    print("Please set api key to environment variable OPENAI_API_KEY")
    sys.exit(1)

openai.api_key = OPENAI_API_KEY

def parse_text(text):
    # 特别注意，需要用pip装上Pygments库才会获得代码高亮特性
    html = markdown.markdown(text, extensions=['fenced_code', CodeHiliteExtension(pygments_style="github-dark", noclasses=True), 'tables'])
    print("markdown converted to html: " + html)
    # 转换后的html传输给前端时，代码块前面的空格会丢失导致缩进失败。需要特殊处理下。
    lines = html.split("\n")
    inside_pre = False
    for i, line in enumerate(lines):
        if "<pre>" in line:
            inside_pre = True
        if "</pre>" in line:
            inside_pre = False
        if inside_pre:
            # 对本行正式内容前面的所有空格，都转为 &nbsp;
            new_line = ""
            for line_i in range(len(line)):
                if line[line_i] == " ":
                    new_line += "&nbsp;"
                else:
                    new_line += line[line_i:]
                    break
            lines[i] = new_line
    html = "<br>".join(lines)
    print("fixed blank issues: " + html)
    return html

def get_response(system, context, raw = False):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[system, *context],
    )
    print(f"response: {response}")

    if raw:
        return response
    else:
        statistics = f'本次对话Tokens用量【{response["usage"]["total_tokens"]} / 4096】 （ 提问+上文 {response["usage"]["prompt_tokens"]}，回答 {response["usage"]["completion_tokens"]} ）'
        message = response["choices"][0]["message"]["content"]

        message_with_stats = f'{message}\n\n================\n\n{statistics}'
#         message_with_stats = markdown.markdown(message_with_stats)

        return message, parse_text(message_with_stats)

def predict(chatbot, input_sentence, system, context):
    if len(input_sentence) == 0:
        return []
    context.append({"role": "user", "content": f"{input_sentence}"})

    message, message_with_stats = get_response(system, context)

    context.append({"role": "assistant", "content": message})

    chatbot.append((input_sentence, message_with_stats))

    return chatbot, context

def retry(chatbot, system, context):
    if len(context) == 0:
        return [], []
    message, message_with_stats = get_response(system, context[:-1])
    context[-1] = {"role": "assistant", "content": message}

    chatbot[-1] = (context[-2]["content"], message_with_stats)
    return chatbot, context

def delete_last_conversation(chatbot, context):
    if len(context) == 0:
        return [], []
    chatbot = chatbot[:-1]
    context = context[:-2]
    return chatbot, context

def reduce_token(chatbot, system, context):
    context.append({"role": "user", "content": "请帮我总结一下上述对话的内容，实现减少tokens的同时，保证对话的质量。在总结中不要加入这一句话。"})

    response = get_response(system, context, raw=True)

    statistics = f'本次对话Tokens用量【{response["usage"]["completion_tokens"]+12+12+8} / 4096】'
    optmz_str = markdown.markdown( f'好的，我们之前聊了:{response["choices"][0]["message"]["content"]}\n\n================\n\n{statistics}' )
    chatbot.append(("请帮我总结一下上述对话的内容，实现减少tokens的同时，保证对话的质量。", optmz_str))
    
    context = []
    context.append({"role": "user", "content": "我们之前聊了什么?"})
    context.append({"role": "assistant", "content": f'我们之前聊了：{response["choices"][0]["message"]["content"]}'})
    return chatbot, context


def reset_state():
    return [], []

def update_system(new_system_prompt):
    return {"role": "system", "content": new_system_prompt}

with gr.Blocks() as demo:
    chatbot = gr.Chatbot().style(color_map=("#1D51EE", "#585A5B"))
    context = gr.State([])
    systemPrompt = gr.State(update_system(initial_prompt))

    with gr.Row():
        with gr.Column(scale=12):
            txt = gr.Textbox(show_label=False, placeholder="在这里输入").style(container=False)
        with gr.Column(min_width=50, scale=1):
            submitBtn = gr.Button("🚀", variant="primary")
    with gr.Row():
        emptyBtn = gr.Button("🧹 新的对话")
        retryBtn = gr.Button("🔄 重新生成")
        delLastBtn = gr.Button("🗑️ 删除上条对话")
        reduceTokenBtn = gr.Button("♻️ 优化Tokens")

    # TODO: prompt 支持自动填充，方便用户选择最适合自己场景的 prompt
    newSystemPrompt = gr.Textbox(show_label=True, placeholder=f"在这里输入新的System Prompt...", label="更改 System prompt").style(container=True)
    systemPromptDisplay = gr.Textbox(show_label=True, value=initial_prompt, interactive=False, label="目前的 System prompt").style(container=True)

    txt.submit(predict, [chatbot, txt, systemPrompt, context], [chatbot, context], show_progress=True)
    txt.submit(lambda :"", None, txt)
    submitBtn.click(predict, [chatbot, txt, systemPrompt, context], [chatbot, context], show_progress=True)
    submitBtn.click(lambda :"", None, txt)
    emptyBtn.click(reset_state, outputs=[chatbot, context])
    newSystemPrompt.submit(update_system, newSystemPrompt, systemPrompt)
    newSystemPrompt.submit(lambda x: x, newSystemPrompt, systemPromptDisplay)
    newSystemPrompt.submit(lambda :"", None, newSystemPrompt)
    retryBtn.click(retry, [chatbot, systemPrompt, context], [chatbot, context], show_progress=True)
    delLastBtn.click(delete_last_conversation, [chatbot, context], [chatbot, context], show_progress=True)
    reduceTokenBtn.click(reduce_token, [chatbot, systemPrompt, context], [chatbot, context], show_progress=True)

def args_parser():
    default_port = 4000
    default_server_name = "0.0.0.0"
    parser = argparse.ArgumentParser(
                    prog = 'ChuanhuChatBot',
                    description = 'GUI for using chatgpt api. '
                                  'Must define api key in environment variable OPENAI_API_KEY first.')
    parser.add_argument('-p', '--port', type=int, default=default_port, help="Listening port. Default is " + str(default_port))
    parser.add_argument('--server_name', type=str, default=default_server_name, help="Server name. Default is " + default_server_name + " which allow visitors visit website from any ip this computer has. If you only allow visiting from current computer, set it to 127.0.0.1")
    parser.add_argument('--username_and_password',
                        nargs='*',
                        help="Username and password for accessing this website. "
                             "Use '/' as split symbol for username and password, and blank between accounts"
                             "Example: 'username/password username2/password2'")

    args = parser.parse_args()
    return args.server_name, args.port, args.username_and_password


if __name__ == "__main__":
    server_name, port, username_and_password = args_parser()
    gr.close_all()
    if username_and_password:
        for i in range(len(username_and_password)):
            username_and_password_tuple = username_and_password[i].split('/')
            if len(username_and_password_tuple) != 2:
                raise ValueError(f"'{username_and_password[i]}' is invalid. Please write as 'username/password'. "
                                 f"Make sure only one '/' exist")
            else:
                username_and_password[i] = username_and_password_tuple
        demo.launch(server_name=server_name, server_port=port, auth=username_and_password)
    else:
        demo.launch(server_name=server_name, server_port=port)
    
