import os
import streamlit as st

try:
    import google.generativeai as genai
except ImportError:
    st.error("google-generativeai 패키지가 설치되지 않았습니다. 다음 명령어로 설치하세요: pip install -U google-generativeai")
    st.stop()

# Configuration
MODEL_ID = "gemini-2.0-flash-exp"  # Try 2.0 exp first, fallback to 1.5 if not available

st.set_page_config(page_title="Gemini Chat · Streamlit", page_icon="💬", layout="centered")

# Read API key priority: Streamlit secrets -> environment -> text input
default_api_key = (
    st.secrets.get("GOOGLE_API_KEY", None)
    if hasattr(st, "secrets")
    else None
) or os.getenv("GOOGLE_API_KEY", "")

st.title("Gemini Chat · Streamlit")
st.caption("Google Generative AI SDK를 사용하여 Gemini 모델을 호출합니다.")

with st.expander("API 키 설정", expanded=not bool(default_api_key)):
    api_key = st.text_input(
        "Google API Key",
        type="password",
        value=default_api_key,
        help="환경변수 GOOGLE_API_KEY 또는 Streamlit Secrets에도 설정할 수 있습니다.",
    )

active_api_key = api_key or default_api_key

if "messages" not in st.session_state:
    st.session_state.messages = []

def add_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})


def call_gemini(prompt: str, api_key: str, model_name: str = MODEL_ID) -> str:
    if not api_key:
        raise ValueError("API 키를 입력하세요.")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.7)
        )
        if not response.text:
            raise RuntimeError("응답을 읽을 수 없습니다.")
        return response.text
    except Exception as e:
        error_msg = str(e)
        # Try fallback model if 2.0 is not available
        if "not found" in error_msg.lower() and model_name == MODEL_ID:
            st.warning(f"{model_name} 모델을 찾을 수 없습니다. gemini-1.5-flash로 재시도합니다...")
            return call_gemini(prompt, api_key, "gemini-1.5-flash")
        raise RuntimeError(f"API 오류: {error_msg}")


st.subheader("연결 상태 확인", divider="gray")
col_test, col_hint = st.columns([1, 2])
with col_test:
    test_btn = st.button("연결 테스트", use_container_width=True)
with col_hint:
    st.caption("짧은 ping 호출로 API 연결을 확인합니다.")

if test_btn:
    try:
        with st.spinner("테스트 호출 중..."):
            _ = call_gemini("ping", active_api_key)
        st.success("API 연결 성공")
    except Exception as e:  # noqa: BLE001
        st.error(f"API 연결 실패: {e}")

# Model selection
with st.expander("모델 선택", expanded=False):
    model_option = st.selectbox(
        "사용할 모델",
        ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"],
        help="gemini-2.0-flash-exp를 먼저 시도하고, 없으면 자동으로 gemini-1.5-flash로 대체됩니다."
    )

st.subheader("채팅", divider="gray")
with st.form("chat_form", clear_on_submit=True):
    prompt = st.text_area("메시지", height=140, placeholder="무엇이든 물어보세요...")
    submitted = st.form_submit_button("Send")

if submitted and prompt.strip():
    add_message("user", prompt)
    try:
        with st.spinner("Gemini 호출 중..."):
            reply = call_gemini(prompt, active_api_key, model_option)
        add_message("assistant", reply)
    except Exception as e:  # noqa: BLE001
        st.error(str(e))

# Render chat history
for msg in st.session_state.messages:
    st.chat_message("assistant" if msg["role"] != "user" else "user").write(msg["content"])

st.caption("API 키는 클라이언트에서만 사용되며 서버에 저장되지 않습니다.")

