import os
import textwrap
import requests
import streamlit as st

# Configuration
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini2.5-flash:generateContent"

st.set_page_config(page_title="Gemini Chat · Streamlit", page_icon="💬", layout="centered")

# Read API key priority: Streamlit secrets -> environment -> text input
default_api_key = (
    st.secrets.get("GOOGLE_API_KEY", None)
    if hasattr(st, "secrets")
    else None
) or os.getenv("GOOGLE_API_KEY", "")

st.title("Gemini Chat · Streamlit")
st.caption("gemini2.5-flash:generateContent 엔드포인트를 호출합니다.")

with st.expander("API 키 설정", expanded=not bool(default_api_key)):
    api_key = st.text_input(
        "Google API Key",
        type="password",
        value=default_api_key,
        help="환경변수 GOOGLE_API_KEY 또는 Streamlit Secrets에도 설정할 수 있습니다.",
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

def add_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})


def call_gemini(prompt: str, api_key: str) -> str:
    if not api_key:
        raise ValueError("API 키를 입력하세요.")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7},
    }

    resp = requests.post(
        f"{API_URL}?key={api_key}",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )

    if not resp.ok:
        # Provide concise error body for debugging
        snippet = textwrap.shorten(resp.text, width=300, placeholder=" ...")
        raise RuntimeError(f"API 오류 {resp.status_code}: {snippet}")

    data = resp.json()
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "\n".join([p.get("text", "") for p in parts]).strip()
    if not text:
        raise RuntimeError("응답을 읽을 수 없습니다.")
    return text


with st.form("chat_form", clear_on_submit=True):
    prompt = st.text_area("메시지", height=140, placeholder="무엇이든 물어보세요...")
    submitted = st.form_submit_button("Send")

if submitted and prompt.strip():
    add_message("user", prompt)
    try:
        with st.spinner("Gemini 호출 중..."):
            reply = call_gemini(prompt, api_key or default_api_key)
        add_message("assistant", reply)
    except Exception as e:  # noqa: BLE001
        st.error(str(e))

# Render chat history
for msg in st.session_state.messages:
    st.chat_message("assistant" if msg["role"] != "user" else "user").write(msg["content"])

st.caption("API 키는 클라이언트에서만 사용되며 서버에 저장되지 않습니다.")

