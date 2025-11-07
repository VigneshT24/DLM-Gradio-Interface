import gradio as gr
from dlm import DLM
import io
import re
from contextlib import redirect_stdout
import textwrap
import os
import base64
current_dir = os.path.dirname(os.path.abspath(__file__))
css_path = os.path.join(current_dir, "style.css")

dlm_bot = DLM("apply", "dlm_knowledge.db")

ansi_escape_pattern = re.compile(r'\x1b\[[0-9;]*m')

try:
    with open("dlm_logo.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    logo_base64 = f"data:image/png;base64,{encoded_string}"
    print("Successfully encoded logo file to Base64.")
except FileNotFoundError:
    print("'dlm_logo.png' NOT FOUND!")
    logo_base64 = "" # Will just show alt text

def get_bot_response(message, history):
    full_response = io.StringIO()

    with redirect_stdout(full_response):
        dlm_bot.ask(message, True)
    clean_response = ansi_escape_pattern.sub('', full_response.getvalue())

    # removing empty lines for easier parsing
    splitted_response = [line for line in clean_response.splitlines() if line.strip()]

    if not splitted_response:
        return "I'm sorry, I couldn't generate a response."

    # The final answer is the last line
    actual_response = splitted_response[-1] 

    # The thoughts are a LIST of all lines *before* the last one
    thought_lines_list = splitted_response[:-1]

    if thought_lines_list:
        thought_html = "<br>".join(thought_lines_list)
        
        html_output = f"""
        <details>
            <summary>Show Thought Process</summary>
            <p>{thought_html}</p> 
        </details>
        <br>
        {actual_response.strip()}
        """
        return textwrap.dedent(html_output)
        
    else:
        # If there were no thoughts, just return the answer
        return actual_response

dlm_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.red,
    secondary_hue=gr.themes.colors.blue,
    font=gr.themes.GoogleFont("Roboto"),
)

with gr.Blocks(
    title="DLM.AI",
    theme="soft",
    css=open("style.css").read()
) as dlm_app:

    # Header / logo section
    gr.HTML(f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
        <img src="{logo_base64}" alt="DLM" style="height:40px;border-radius:8px;">
        <h2 style="margin:0;color:#e5e7eb;font-family:Inter;">College Knowledge Bot - Powered by DLM.AI</h2>
    </div>
    """)

    chatbot = gr.Chatbot(label=None, show_label=False)
    msg = gr.Textbox(placeholder="Ask me anything related to college FAQs...", lines=1)

    def respond(message, history):
        bot_reply = get_bot_response(message, history)
        history.append((message, bot_reply))
        return "", history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])

dlm_app.launch(favicon_path="dlm_logo.png", allowed_paths=["dlm_logo.png"], pwa=True)
