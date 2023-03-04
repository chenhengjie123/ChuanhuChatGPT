import gradio as gr
import openai
import os
import sys
import markdown

import argparse

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
initial_prompt = "You are a helpful assistant."


if OPENAI_API_KEY == "empty":
    print("Please set api key to environment variable OPENAI_API_KEY")
    sys.exit(1)

openai.api_key = OPENAI_API_KEY

def parse_text(text):
    # 特别注意，需要用pip装上Pygments库才会获得代码高亮特性
    return markdown.markdown(text, extensions=['fenced_code', 'codehilite', 'tables'])

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

# 代码着色的 css 可参照：https://richleland.github.io/pygments-css/ 进行生成。这里用的是 vim 主题
with gr.Blocks(css="""
.codehilite .hll { background-color: #222222 }
.codehilite  { background: #000000; color: #cccccc }
.codehilite .c { color: #000080 } /* Comment */
.codehilite .err { color: #cccccc; border: 1px solid #FF0000 } /* Error */
.codehilite .esc { color: #cccccc } /* Escape */
.codehilite .g { color: #cccccc } /* Generic */
.codehilite .k { color: #cdcd00 } /* Keyword */
.codehilite .l { color: #cccccc } /* Literal */
.codehilite .n { color: #cccccc } /* Name */
.codehilite .o { color: #3399cc } /* Operator */
.codehilite .x { color: #cccccc } /* Other */
.codehilite .p { color: #cccccc } /* Punctuation */
.codehilite .ch { color: #000080 } /* Comment.Hashbang */
.codehilite .cm { color: #000080 } /* Comment.Multiline */
.codehilite .cp { color: #000080 } /* Comment.Preproc */
.codehilite .cpf { color: #000080 } /* Comment.PreprocFile */
.codehilite .c1 { color: #000080 } /* Comment.Single */
.codehilite .cs { color: #cd0000; font-weight: bold } /* Comment.Special */
.codehilite .gd { color: #cd0000 } /* Generic.Deleted */
.codehilite .ge { color: #cccccc; font-style: italic } /* Generic.Emph */
.codehilite .gr { color: #FF0000 } /* Generic.Error */
.codehilite .gh { color: #000080; font-weight: bold } /* Generic.Heading */
.codehilite .gi { color: #00cd00 } /* Generic.Inserted */
.codehilite .go { color: #888888 } /* Generic.Output */
.codehilite .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
.codehilite .gs { color: #cccccc; font-weight: bold } /* Generic.Strong */
.codehilite .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
.codehilite .gt { color: #0044DD } /* Generic.Traceback */
.codehilite .kc { color: #cdcd00 } /* Keyword.Constant */
.codehilite .kd { color: #00cd00 } /* Keyword.Declaration */
.codehilite .kn { color: #cd00cd } /* Keyword.Namespace */
.codehilite .kp { color: #cdcd00 } /* Keyword.Pseudo */
.codehilite .kr { color: #cdcd00 } /* Keyword.Reserved */
.codehilite .kt { color: #00cd00 } /* Keyword.Type */
.codehilite .ld { color: #cccccc } /* Literal.Date */
.codehilite .m { color: #cd00cd } /* Literal.Number */
.codehilite .s { color: #cd0000 } /* Literal.String */
.codehilite .na { color: #cccccc } /* Name.Attribute */
.codehilite .nb { color: #cd00cd } /* Name.Builtin */
.codehilite .nc { color: #00cdcd } /* Name.Class */
.codehilite .no { color: #cccccc } /* Name.Constant */
.codehilite .nd { color: #cccccc } /* Name.Decorator */
.codehilite .ni { color: #cccccc } /* Name.Entity */
.codehilite .ne { color: #666699; font-weight: bold } /* Name.Exception */
.codehilite .nf { color: #cccccc } /* Name.Function */
.codehilite .nl { color: #cccccc } /* Name.Label */
.codehilite .nn { color: #cccccc } /* Name.Namespace */
.codehilite .nx { color: #cccccc } /* Name.Other */
.codehilite .py { color: #cccccc } /* Name.Property */
.codehilite .nt { color: #cccccc } /* Name.Tag */
.codehilite .nv { color: #00cdcd } /* Name.Variable */
.codehilite .ow { color: #cdcd00 } /* Operator.Word */
.codehilite .w { color: #cccccc } /* Text.Whitespace */
.codehilite .mb { color: #cd00cd } /* Literal.Number.Bin */
.codehilite .mf { color: #cd00cd } /* Literal.Number.Float */
.codehilite .mh { color: #cd00cd } /* Literal.Number.Hex */
.codehilite .mi { color: #cd00cd } /* Literal.Number.Integer */
.codehilite .mo { color: #cd00cd } /* Literal.Number.Oct */
.codehilite .sa { color: #cd0000 } /* Literal.String.Affix */
.codehilite .sb { color: #cd0000 } /* Literal.String.Backtick */
.codehilite .sc { color: #cd0000 } /* Literal.String.Char */
.codehilite .dl { color: #cd0000 } /* Literal.String.Delimiter */
.codehilite .sd { color: #cd0000 } /* Literal.String.Doc */
.codehilite .s2 { color: #cd0000 } /* Literal.String.Double */
.codehilite .se { color: #cd0000 } /* Literal.String.Escape */
.codehilite .sh { color: #cd0000 } /* Literal.String.Heredoc */
.codehilite .si { color: #cd0000 } /* Literal.String.Interpol */
.codehilite .sx { color: #cd0000 } /* Literal.String.Other */
.codehilite .sr { color: #cd0000 } /* Literal.String.Regex */
.codehilite .s1 { color: #cd0000 } /* Literal.String.Single */
.codehilite .ss { color: #cd0000 } /* Literal.String.Symbol */
.codehilite .bp { color: #cd00cd } /* Name.Builtin.Pseudo */
.codehilite .fm { color: #cccccc } /* Name.Function.Magic */
.codehilite .vc { color: #00cdcd } /* Name.Variable.Class */
.codehilite .vg { color: #00cdcd } /* Name.Variable.Global */
.codehilite .vi { color: #00cdcd } /* Name.Variable.Instance */
.codehilite .vm { color: #00cdcd } /* Name.Variable.Magic */
.codehilite .il { color: #cd00cd } /* Literal.Number.Integer.Long */
""") as demo:
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
                    description = 'GUI for using chatgpt api. Must define api key in environment variable OPENAI_API_KEY first.')
    parser.add_argument('-p', '--port', type=int, default=default_port, help="Listening port. Default is " + str(default_port))
    parser.add_argument('--server_name', type=str, default=default_server_name, help="Server name. Default is " + default_server_name + " which allow visitors visit website from any ip this computer has. If you only allow visiting from current computer, set it to 127.0.0.1")
    parser.add_argument('--username', help="Username for accessing this website. Leave it empty if you don't need it.")
    parser.add_argument('--password', help="Password for accessing this website. Leave it empty if you don't need it.")

    args = parser.parse_args()
    return args.server_name, args.port, args.username, args.password


if __name__ == "__main__":
    server_name, port, username, password = args_parser()
    if username and password:
        demo.launch(server_name=server_name, server_port=port, auth=(username, password))
    else:
        demo.launch(server_name=server_name, server_port=port)
    
