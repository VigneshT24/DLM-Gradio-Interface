import gradio as gr
from dlm import DLM
import io
import re
from contextlib import redirect_stdout

dlm_bot = DLM("apply", "dlm_knowledge.db")

ansi_escape_pattern = re.compile(r'\x1b\[[0-9;]*m')

def get_bot_response(message, history):
    temp_f = io.StringIO()

    with redirect_stdout(temp_f):
        dlm_bot.ask(message, True)
    clean_response = ansi_escape_pattern.sub('', temp_f.getvalue())

    return clean_response.strip()

dlm_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.red,
    secondary_hue=gr.themes.colors.blue,
    font=gr.themes.GoogleFont("Inter")
)

dlm_app = gr.ChatInterface(fn=get_bot_response, 
                            title="DLM.AI",
                            theme=dlm_theme)

dlm_app.launch(favicon_path="dlm_logo.png")
