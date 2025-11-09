import gradio as gr
from dlm import DLM
import io
import re
from contextlib import redirect_stdout
import textwrap
import os
import base64
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
css_path = os.path.join(current_dir, "style.css")

dlm_bot = DLM("apply", "dlm_knowledge.db")

ansi_escape_pattern = re.compile(r'\x1b\[[0-9;]*m')

# Session storage for chat history (clears on refresh)
chat_sessions = {}
current_session_id = None

# Try-Expect block is to encode logo image to Base64 for faster image processing
try:
    with open("dlm_logo.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    logo_base64 = f"data:image/png;base64,{encoded_string}"
    print("Successfully encoded logo file to Base64.")
except FileNotFoundError:
    print("'dlm_logo.png' NOT FOUND!")
    logo_base64 = ""

def create_new_session():
    """Create a new chat session with a unique ID."""
    global current_session_id
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    current_session_id = session_id
    chat_sessions[session_id] = {
        "history": [],
        "title": "New Chat",
        "timestamp": datetime.now().isoformat()
    }
    return session_id

def get_session_title(history):
    """Generate a title from the first user message."""
    if history and len(history) > 0:
        first_message = history[0][0]
        return first_message[:40] + "..." if len(first_message) > 40 else first_message
    return "New Chat"

def get_session_list():
    """Get list of sessions for the radio buttons."""
    if not chat_sessions:
        return []
    
    choices = []
    for session_id, session_data in sorted(chat_sessions.items(), reverse=True):
        timestamp = datetime.fromisoformat(session_data["timestamp"])
        time_str = timestamp.strftime("%m/%d %H:%M")
        title = session_data['title']
        label = f"{time_str} - {title}"
        choices.append((label, session_id))
    
    return choices

def save_current_session(history):
    """Save the current chat history to the session."""
    global current_session_id
    if current_session_id and history:
        chat_sessions[current_session_id]["history"] = history
        chat_sessions[current_session_id]["title"] = get_session_title(history)

def start_new_chat():
    """Start a new chat session."""
    create_new_session()
    return [], gr.update(choices=get_session_list(), value=None), gr.update(visible=False)

def load_selected_session(session_id):
    """Load a selected chat session."""
    global current_session_id
    if session_id and session_id in chat_sessions:
        current_session_id = session_id
        return chat_sessions[session_id]["history"], gr.update(visible=False)
    return [], gr.update(visible=False)

def toggle_sidebar(current_visibility):
    """Toggle sidebar visibility."""
    return gr.update(visible=not current_visibility)

def get_bot_response(message, history):
    """Get the bot's response to a user message."""
    if message is None or message.strip() == "":
        return "Friendly reminder: empty messages won't get a response. Please type something!"
    
    save_current_session(history)
    
    full_response = io.StringIO()
    with redirect_stdout(full_response):
        dlm_bot.ask(message, True)
    clean_response = ansi_escape_pattern.sub('', full_response.getvalue())

    clean_response = ansi_escape_pattern.sub('', full_response.getvalue())
    splitted_response = [line for line in clean_response.splitlines() if line.strip()]

    if not splitted_response:
        return "I'm sorry, I couldn't generate a response."

    actual_response = splitted_response[-1] 
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
        return actual_response

# Custom CSS
custom_css = """
#history-btn {
    position: fixed;
    top: 30px;
    left: 50px;
    z-index: 1001;
    width: 50px;
    height: 50px;
    border-radius: 10px;
    background: #2d2f36 !important;
    border: 1px solid #FFA500 !important;
    color: #FFA500 !important;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 24px;
}

#history-btn:hover {
    background: #FFA500 !important;
    color: #1a1c22 !important;
    transform: scale(1.05);
}

#sidebar-column {
    background: #1a1c22;
    border-right: 2px solid #2d2f36;
    padding: 20px;
    height: 100vh;
    overflow-y: auto;
}

#new-chat-btn {
    width: 100%;
    margin-bottom: 20px;
    background: #FFA500 !important;
    border: none !important;
    color: #1a1c22 !important;
    font-weight: 600 !important;
}

#close-sidebar-btn {
    width: 100%;
    margin-bottom: 10px;
    background: transparent !important;
    border: 1px solid #FFA500 !important;
    color: #FFA500 !important;
}

#history-radio label {
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 5px;
    cursor: pointer;
    background: #2d2f36;
    transition: background 0.2s;
}

#history-radio label:hover {
    background: #3a3c44;
}
"""

try:
    with open("style.css", "r") as f:
        existing_css = f.read()
    combined_css = existing_css + "\n" + custom_css
except FileNotFoundError:
    combined_css = custom_css

with gr.Blocks(title="DLM.AI", theme="citrus", css=combined_css) as dlm_app:
    
    sidebar_visible = gr.State(False)
    
    # Terms and Conditions Screen
    with gr.Column(visible=True, elem_id="terms_screen") as terms_screen:
        gr.HTML("""
        <div style="display: flex; justify-content: center; align-items: center; height: 80vh;">
            <div style="background: #1a1c22; border: 1px solid #2d2f36; border-radius: 14px; padding: 30px; width: 60%; max-width: 600px; color: #e5e7eb; font-family: 'Inter', sans-serif; text-align: left; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <h2 style="color: #FFA500; text-align:center; margin-bottom: 12px;">Terms & Conditions</h2>
                <p style="line-height: 1.6;">By using <strong>DLM.AI</strong>, you agree that your input data may be processed for educational and research purposes. Although the bot doesn't use your queries to train its models, <strong>please avoid sharing sensitive or personal information</strong> for your own privacy and security.</p>
                <p style="line-height: 1.6; margin-top: 16px;"><strong>Quick Terms:</strong></p>
                <ul style="line-height: 1.6; margin-left: 20px; margin-top: 8px; font-weight: normal;">
                    <li style="font-weight: normal; margin-bottom: 8px;">DLM can provide inaccurate or outdated information. Always verify.</li>
                    <li style="font-weight: normal; margin-bottom: 8px;">DLM is not liable for any decisions made based on its responses.</li>
                    <li style="font-weight: normal; margin-bottom: 8px;">DLM is not a substitute for professional advice.</li>
                </ul>
                <p style="line-height: 1.6; margin-top: 16px; font-weight: normal;">Responses are generated using a Hybrid AI Architecture that combines rule-based logic with existing machine learning models, so occasional inconsistencies may occur. If you have any questions, please contact me <a href="mailto:vignesh.tho2006@gmail.com" style="color: #FFA500; text-decoration: underline;">using this link</a>.</p>
                <p style="text-align:left; font-size:0.9rem; color:#9ca3af; margin-top:20px;">© 2025 Vignesh Thondikulam (DLM.AI). All rights reserved.</p>
            </div>
        </div>
        """)
    
    agree_btn = gr.Button("I Agree", elem_id="agree-btn", variant="primary")

    with gr.Group(visible=False) as chat_screen:
        info_text = gr.Markdown(visible=False)
        with gr.Row():
            # Sidebar
            with gr.Column(scale=1, visible=False, elem_id="sidebar-column") as sidebar:
                close_sidebar_btn = gr.Button("✕ Close", elem_id="close-sidebar-btn")
                new_chat_btn = gr.Button("✛ New Chat", elem_id="new-chat-btn", variant="primary")
                info_btn = gr.Button("Info", elem_id="info-btn")

                info_visible = gr.State(False)

                def toggle_info(current_visibility):
                    """Toggles the info window visibility and hides 'Previous Chats' when visible."""
                    show_info = not current_visibility
                    return (
                        show_info,                                 # new state value
                        gr.update(visible=show_info),              # info popup visibility
                        gr.update(visible=not show_info)           # hide/show history radio
                    )

                # Create the popup content (initially hidden)
                with gr.Column(visible=False, elem_id="info-popup") as info_popup:
                    gr.HTML("""
                    <div style="
                        background: #1a1c22;
                        border: 1px solid #2d2f36;
                        border-radius: 12px;
                        padding: 24px;
                        width: 100%;
                        max-width: none;
                        margin: 20px 0;
                        color: #f3f4f6;
                        text-align: left;
                        font-family: 'Inter', sans-serif;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
                    ">
                        <h3 style="color:#FFA500; text-align:left;">About DLM.AI</h3>
                        <p style="line-height:1.6;">
                            <strong>DLM.AI</strong> is an AI assistant built for domain-specific reasoning and computation. 
                            In this app, it focuses on college-related queries but can adapt to any field. 
                            Using a <strong>Hybrid AI architecture</strong> with <strong>SpaCy</strong> and <strong>HuggingFace Transformers</strong>, 
                            it combines rule-based logic and machine learning for accuracy and context awareness. 
                            Its <strong>Auto-Routing</strong> system switches between <em>Memory</em> and <em>Compute</em> models depending on the query. 
                            As with any AI, occasional inaccuracies may occur.
                        </p>
                        <p style="margin-top:12px; font-size:0.9rem; color:#9ca3af;">
                            © 2025 Vignesh Thondikulam (DLM.AI). All rights reserved.
                        </p>
                    </div>
                    """)
                
                # Previous Chats Radio
                history_radio = gr.Radio(
                    choices=[],
                    label="Previous Chats (Only This Session)",
                    elem_id="history-radio",
                    interactive=True
                )

                # When "Info" is clicked → toggle the popup & hide 'Previous Chats'
                info_btn.click(
                    fn=toggle_info,
                    inputs=[info_visible],
                    outputs=[info_visible, info_popup, history_radio]
                )
            
            # Main chat area
            with gr.Column(scale=4):
                # Hamburger button
                history_btn = gr.Button("☰", elem_id="history-btn", size="sm")
                
                # Header
                gr.HTML(f"""
                <div style="display: flex; align-items: center; justify-content: flex-end; gap: 14px; margin-bottom: 20px; padding: 6px 0;">
                    <h1 style='margin: 0; color: #f3f4f6; font-family: "Poppins", "Inter", sans-serif; font-weight: 600; font-size: 1.7rem; letter-spacing: 0.6px;'>
                        <span style="color:#FFA500;">DLM.AI</span> | College Knowledge Assistant
                    </h1>
                    <img src='{logo_base64}' alt='DLM Logo' style='height:45px;border-radius:10px;'>
                </div>
                """)

                chatbot = gr.Chatbot(label=None, show_label=False)
                msg = gr.Textbox(placeholder="Ask me anything related to college or basic computation queries...", lines=1)

    def respond(message, history):
        """Handles user input and generates bot response."""
        global current_session_id
        if current_session_id is None:
            create_new_session()
        
        bot_reply = get_bot_response(message, history)
        history.append((message, bot_reply))
        save_current_session(history)
        
        return "", history, gr.update(choices=get_session_list())

    # Event handlers
    msg.submit(respond, [msg, chatbot], [msg, chatbot, history_radio])
    
    history_btn.click(
        lambda: (gr.update(visible=True), gr.update(visible=False), True),
        None,
        [sidebar, history_btn, sidebar_visible]
    )
    
    close_sidebar_btn.click(
        lambda: (gr.update(visible=False), gr.update(visible=True), False),
        None,
        [sidebar, history_btn, sidebar_visible]
    )
    
    new_chat_btn.click(
        start_new_chat,
        None,
        [chatbot, history_radio, sidebar]
    ).then(
        lambda: (gr.update(visible=True), False),
        None,
        [history_btn, sidebar_visible]
    )
    
    history_radio.change(
        load_selected_session,
        [history_radio],
        [chatbot, sidebar]
    ).then(
        lambda: (gr.update(visible=True), False),
        None,
        [history_btn, sidebar_visible]
    )

    # Agree button
    def on_agree():
        create_new_session()
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(choices=get_session_list())
        )

    agree_btn.click(
        on_agree,
        None,
        [terms_screen, chat_screen, agree_btn, history_radio]
    )

dlm_app.launch(favicon_path="dlm_logo.png", allowed_paths=["dlm_logo.png"], pwa=True)
