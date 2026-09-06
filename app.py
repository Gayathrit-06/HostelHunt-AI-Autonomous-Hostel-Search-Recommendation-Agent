import streamlit as st
import json
import os
import uuid
import re
from langchain_core.messages import HumanMessage
from backend.agent import agent_executor

# File to store chat history locally on your machine
STORAGE_FILE = "chat_history.json"

# Page configuration
st.set_page_config(
    page_title="HostelHunt AI",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Dark Theme & Links
st.markdown("""
    <style>
    /* Dark Theme Base */
    .stApp {
        background-color: #0D1117;
        color: #E6EDF3;
    }

    /* Vibrant Title */
    .title-text {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF007F 0%, #7928CA 50%, #00F2FE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }

    .sub-text {
        color: #8B949E;
        font-size: 1.0rem;
        margin-bottom: 1.5rem;
    }

    /* Message Cards */
    .user-card {
        background: #161B22;
        border-left: 4px solid #00F2FE;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
        color: #FFFFFF;
    }

    .bot-card {
        background: #161B22;
        border-left: 4px solid #FF007F;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 15px;
        line-height: 1.6;
    }

    /* Target _blank links styling */
    .ext-link {
        color: #58A6FF !important;
        text-decoration: underline !important;
        font-weight: 600;
    }
    .ext-link:hover {
        color: #79C0FF !important;
    }

    .map-btn {
        display: inline-block;
        background: linear-gradient(90deg, #FF007F 0%, #7928CA 100%);
        color: #FFFFFF !important;
        font-weight: 600;
        padding: 6px 14px;
        border-radius: 6px;
        text-decoration: none !important;
        margin-top: 6px;
        margin-bottom: 6px;
        box-shadow: 0 2px 8px rgba(255, 0, 127, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# Local JSON Storage Helpers (Persist history on restart)
# ----------------------------------------------------
def load_chats_from_file():
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    default_id = str(uuid.uuid4())
    return {
        default_id: {"title": "New Chat", "messages": []}
    }

def save_chats_to_file(chats_dict):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(chats_dict, f, ensure_ascii=False, indent=2)

# Helper Function: Extract clean text from agent response
def get_clean_text(message_obj):
    if hasattr(message_obj, "content"):
        return message_obj.content
    elif isinstance(message_obj, tuple):
        return message_obj[1]
    return str(message_obj)

# Helper Function: Convert ALL URLs and Markdown links into target="_blank" HTML links
def format_bot_response(text):
    # 1. Convert Markdown links [text](url) -> HTML link with target="_blank"
    def md_link_replacer(match):
        label = match.group(1)
        url = match.group(2)
        if "maps" in url.lower() or "google.com/maps" in url.lower():
            return f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="map-btn">📍 {label}</a>'
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="ext-link">{label}</a>'

    formatted = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', md_link_replacer, text)

    # 2. Convert remaining raw URLs https://... -> HTML link with target="_blank"
    def raw_url_replacer(match):
        url = match.group(0)
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="ext-link">{url}</a>'

    # Match URLs not already inside an href="" attribute
    formatted = re.sub(r'(?<!href=")(https?://[^\s<>"]+)', raw_url_replacer, formatted)

    # 3. Handle bold text and newlines cleanly
    formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', formatted)
    formatted = formatted.replace("\n", "<br>")

    return formatted

# ----------------------------------------------------
# Initialize Session State
# ----------------------------------------------------
if "chats" not in st.session_state:
    st.session_state.chats = load_chats_from_file()

if "current_chat_id" not in st.session_state or st.session_state.current_chat_id not in st.session_state.chats:
    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]

if "editing_chat_id" not in st.session_state:
    st.session_state.editing_chat_id = None

current_id = st.session_state.current_chat_id

# ----------------------------------------------------
# Sidebar: Persistent Chat History Navigation
# ----------------------------------------------------
with st.sidebar:
    st.markdown("### 💬 Chat History")
    
    # "+ New Chat" Button
    if st.button("➕ New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {
            "title": f"Chat {len(st.session_state.chats) + 1}",
            "messages": []
        }
        st.session_state.current_chat_id = new_id
        save_chats_to_file(st.session_state.chats)
        st.rerun()

    st.markdown("---")

    # Display all chats in sidebar
    chat_ids = list(st.session_state.chats.keys())
    for c_id in chat_ids:
        chat_data = st.session_state.chats[c_id]
        is_active = (c_id == current_id)
        
        col_title, col_opts = st.columns([0.75, 0.25])
        
        with col_title:
            prefix = "🟢 " if is_active else "💬 "
            if st.button(f"{prefix}{chat_data['title']}", key=f"select_{c_id}", use_container_width=True):
                st.session_state.current_chat_id = c_id
                st.rerun()

        with col_opts:
            # 3-dot option popover
            with st.popover("⋮"):
                st.caption("Options")
                if st.button("✏️ Rename", key=f"rename_btn_{c_id}"):
                    st.session_state.editing_chat_id = c_id
                    st.rerun()
                
                if st.button("🗑️ Delete", key=f"del_btn_{c_id}"):
                    if len(st.session_state.chats) > 1:
                        del st.session_state.chats[c_id]
                        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                        save_chats_to_file(st.session_state.chats)
                        st.rerun()
                    else:
                        st.warning("Cannot delete the only chat.")

    # Inline Rename Prompt
    if st.session_state.editing_chat_id:
        edit_id = st.session_state.editing_chat_id
        if edit_id in st.session_state.chats:
            st.markdown("---")
            new_name = st.text_input("New Title:", value=st.session_state.chats[edit_id]["title"])
            c_save, c_cancel = st.columns(2)
            with c_save:
                if st.button("Save Name"):
                    st.session_state.chats[edit_id]["title"] = new_name
                    st.session_state.editing_chat_id = None
                    save_chats_to_file(st.session_state.chats)
                    st.rerun()
            with c_cancel:
                if st.button("Cancel"):
                    st.session_state.editing_chat_id = None
                    st.rerun()

# ----------------------------------------------------
# Main Interface
# ----------------------------------------------------
st.markdown('<p class="title-text">🏠 HostelHunt AI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Smart Search Engine for Hostels & PGs across India</p>', unsafe_allow_html=True)

# Render Messages of Active Chat
active_messages = st.session_state.chats[current_id]["messages"]

for msg in active_messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-card"><b>👤 You:</b> {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        formatted_html = format_bot_response(msg["content"])
        st.markdown(f'<div class="bot-card"><b>🤖 HostelHunt:</b><br>{formatted_html}</div>', unsafe_allow_html=True)

# Handle Query Input
user_query = st.chat_input("Ask HostelMate (e.g., Find 3 hostels near CMC Vellore)...")

if user_query:
    # 1. Add User Message
    st.session_state.chats[current_id]["messages"].append({"role": "user", "content": user_query})
    
    # Auto-rename "New Chat" title on first prompt
    if len(active_messages) == 1 or "New Chat" in st.session_state.chats[current_id]["title"]:
        st.session_state.chats[current_id]["title"] = user_query[:22] + "..."

    save_chats_to_file(st.session_state.chats)

    # 2. Call Agent
    with st.spinner("🤖 Searching best hostels..."):
        try:
            response = agent_executor.invoke({"messages": [HumanMessage(content=user_query)]})
            bot_text = get_clean_text(response["messages"][-1])
            
            # 3. Save Bot Response
            st.session_state.chats[current_id]["messages"].append({"role": "assistant", "content": bot_text})
            save_chats_to_file(st.session_state.chats)
            st.rerun()

        except Exception as e:
            st.error(f"Execution Error: {e}")