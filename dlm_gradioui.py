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

# Try-Expect block is to encode logo image to Base64 for faster image processing
try:
    with open("dlm_logo.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    logo_base64 = f"data:image/png;base64,{encoded_string}"
    print("Successfully encoded logo file to Base64.")
except FileNotFoundError:
    print("'dlm_logo.png' NOT FOUND!")
    logo_base64 = "" # Will just show alt text

def get_bot_response(message, history):
    """
        Get the bot's response to a user message, capturing its thought process.

        Parameters:
            message (str): The user's input message.
            history (list): The chat history.

        Behavior:
            - Captures all printed output from the bot, cleans it of ANSI escape codes,
              and separates the thought process from the final answer.
    """
    # convert terminal void outpput to string
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

# sets the general theme for the app
dlm_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.red,
    secondary_hue=gr.themes.colors.blue,
    font=gr.themes.GoogleFont("Roboto"),
)

# builds the Gradio app UI
with gr.Blocks(
    title="DLM.AI",
    theme="citrus",
    css=open("style.css").read()
) as dlm_app:
    
    # Terms and Conditions Screen
    with gr.Column(visible=True, elem_id="terms_screen") as terms_screen:
        gr.HTML("""
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: 80vh;
        ">
            <div style="
                background: #1a1c22;
                border: 1px solid #2d2f36;
                border-radius: 14px;
                padding: 30px;
                width: 60%;
                max-width: 600px;
                color: #e5e7eb;
                font-family: 'Inter', sans-serif;
                text-align: left;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            ">
                <h2 style="color: #FFA500; text-align:center; margin-bottom: 12px;">Terms & Conditions</h2>
                <p style="line-height: 1.6;">
                    By using <strong>DLM.AI</strong>, you agree that your input data may be processed
                    for educational and research purposes. Although the bot doesn't use your queries to train its models,
                    <strong>please avoid sharing sensitive or personal information<strong> for your own privacy and security. 
                </p>
                
                <p style="line-height: 1.6; margin-top: 16px;"><strong>Quick Terms:</strong></p>
                <ul style="line-height: 1.6; margin-left: 20px; margin-top: 8px; font-weight: normal;">
                    <li style="font-weight: normal; margin-bottom: 8px;">DLM can provide inaccurate or outdated information. Always verify.</li>
                    <li style="font-weight: normal; margin-bottom: 8px;">DLM is not liable for any decisions made based on its responses.</li>
                    <li style="font-weight: normal; margin-bottom: 8px;">DLM is not a substitute for professional advice.</li>
                </ul>
                
                <p style="line-height: 1.6; margin-top: 16px; font-weight: normal;">
                    Responses are generated using a Hybrid AI Architecture that combines rule-based logic with existing machine learning models, so occasional inconsistencies may occur.
                    If you have any questions, please contact me <a href="mailto:vignesh.tho2006@gmail.com" style="color: #FFA500; text-decoration: underline;">using this link</a>.
                </p>

                <p style="text-align:left; font-size:0.9rem; color:#9ca3af; margin-top:20px;">
                    © 2025 Vignesh Thondikulam (DLM.AI). All rights reserved.
                </p>
            </div>
        </div>
        """)
    
    # Create a visible button that users actually click
    agree_btn = gr.Button("I Agree", elem_id="agree-btn", variant="primary")

    with gr.Group(visible=False) as chat_screen:
    # more customized header with logo and title using HTML
        gr.HTML(f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            margin-bottom: 20px;
            padding: 6px 0;
        ">
            <img src='{logo_base64}' alt='DLM Logo' style='height:45px;border-radius:10px;'>
            <h1 style='
                margin: 0;
                color: #f3f4f6;
                font-family: "Poppins", "Inter", sans-serif;
                font-weight: 600;
                font-size: 1.7rem;
                letter-spacing: 0.6px;
            '>
                <span style="color:#FFA500;">DLM.AI</span> | College Knowledge Assistant
            </h1>
        </div>
        """)

        # chatbot interface
        chatbot = gr.Chatbot(label=None, show_label=False)

        # user input textbox
        msg = gr.Textbox(placeholder="Ask me anything related to college or basic computation queries...", lines=1)

        def respond(message, history):
            """Handles user input and generates bot response, updating chat history."""
            bot_reply = get_bot_response(message, history)
            history.append((message, bot_reply))
            return "", history

        msg.submit(respond, [msg, chatbot], [msg, chatbot])

    # when "I Agree" is clicked, show chat screen and hide terms
    agree_btn.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)),
        inputs=None,
        outputs=[terms_screen, chat_screen, agree_btn]
    )

# launch the app with PWA support and custom favicon
dlm_app.launch(favicon_path="dlm_logo.png", allowed_paths=["dlm_logo.png"], pwa=True)
