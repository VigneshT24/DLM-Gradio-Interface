import gradio as gr
from dlm import DLM
import io
import re
from contextlib import redirect_stdout

dlm_bot = DLM("apply", "dlm_knowledge.db")

ansi_escape_pattern = re.compile(r'\x1b\[[0-9;]*m')

def get_bot_response(message):
    full_response = io.StringIO()
    thought_text = "" # to seperate the COT from the final answer
    actual_response = "" # to seperate the final answer from the COT

    with redirect_stdout(full_response):
        dlm_bot.ask(message, True)
    clean_response = ansi_escape_pattern.sub('', full_response.getvalue())

    # removing empty lines for easier parsing
    splitted_response = [line for line in clean_response.splitlines() if line.strip()]

    actual_response = splitted_response[len(splitted_response) - 1]

    for line in splitted_response[:-1]:
        thought_text += line + " "

    # as of now, just seperated the COT and final answer
    # need to have the model output the COT inside a openable container
    print("THOUGHTS:" + str(thought_text))
    print("RESPONSE:" + actual_response)

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
