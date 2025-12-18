import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta
import calendar
import random

# --- 데이터베이스 함수 정의 ---
def init_db():
    #앱 실행 시 필요한 데이터베이스와 테이블(사용자, 소비 기록, 위시리스트)을 자동으로 생성한다. 
    #'money_manager.db' 파일이 생성되고, 사용자가 입력한 데이터를 영구적으로 저장할 공간이 생긴다.
    
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    # 사용자 테이블 (닉네임, 비밀번호)
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, pin TEXT)''')
    # 소비 기록 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, 
                  date TEXT, 
                  item TEXT, 
                  price INTEGER, 
                  category TEXT, 
                  type TEXT)''')
    # 위시리스트 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS wishlist
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, 
                  item_name TEXT, 
                  target_price INTEGER, 
                  image_data BLOB)''')
    
    # 게이미피케이션을 위한 컬럼 추가 (기존 DB 호환성 유지)
    # 게이미피케이션(XP, 포인트, 스트릭) 기능을 위해 기존 DB 구조를 업데이트한다.
    # 기존에 앱을 쓰던 사용자도 데이터 손실 없이 새로운 게임 요소(레벨업 등)를 즐길 수 있도록 한다.
    try:
        c.execute("ALTER TABLE users ADD COLUMN last_active_date TEXT")
    except sqlite3.OperationalError: pass
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN streak_days INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass

    conn.commit()
    conn.close()

def login_user(username, pin):
    #로그인 및 자동 회원가입 로직을 처리한다. 
    #DB에 없는 닉네임이면 자동으로 가입시켜 초등학생들이 복잡한 절차 없이 바로 앱을 사용할 수 있게 한다.
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    c.execute('SELECT pin FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    if result:
        return (True, "로그인 성공! 어서와요!") if result[0] == pin else (False, "비밀번호가 틀렸어요. 다시 확인해볼까요?")
    else:
        # 신규 유저 자동 가입
        conn = sqlite3.connect('money_manager.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (username, pin) VALUES (?, ?)', (username, pin))
        conn.commit()
        conn.close()
        return True, "새로운 친구 환영해요! 가입이 완료되었어요!"

def update_user_activity(username, xp_gain=10, points_gain=10):
    #사용자가 소비를 기록할 때마다 보상(XP, 포인트)을 지급하고 연속 접속일(Streak)을 계산한다.
    #'정의적 비계'로서 학생들에게 지속적인 학습 동기를 부여한다.
    """활동 기록 시 스트릭, 경험치, 포인트 업데이트"""
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    
    # 현재 유저 정보 조회
    c.execute('SELECT last_active_date, streak_days, xp, points FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    
    if row:
        last_date_str, streak, xp, points = row
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # 경험치 및 포인트 증가
        new_xp = (xp if xp else 0) + xp_gain
        new_points = (points if points else 0) + points_gain
        
        # 스트릭 계산
        new_streak = streak if streak else 0
        if last_date_str != today_str:
            if last_date_str:
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
                if (datetime.now() - last_date).days == 1:
                    new_streak += 1 # 연속 기록
                else:
                    new_streak = 1 # 끊김, 다시 시작
            else:
                new_streak = 1 # 첫 기록
        
        c.execute('UPDATE users SET last_active_date = ?, streak_days = ?, xp = ?, points = ? WHERE username = ?', 
                  (today_str, new_streak, new_xp, new_points, username))
    
    conn.commit()
    conn.close()

def get_user_stats(username):
    #사용자의 현재 레벨과 랭킹 정보를 표시하기 위해 DB에서 데이터를 조회한다.
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    c.execute('SELECT streak_days, xp, points FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result if result else (0, 0, 0)

def get_leaderboard():
    #사회적 모델링를 통해 포인트가 높은 상위 5명의 친구 목록을 가져온다.
    conn = sqlite3.connect('money_manager.db')
    # 포인트 순으로 상위 5명 조회
    df = pd.read_sql_query("SELECT username, xp, points FROM users ORDER BY points DESC LIMIT 5", conn)
    conn.close()
    return df

def add_expense_db(username, date, item, price, category, type_val):
    #소비 내역(날짜, 항목, 금액, Need/Want 여부)을 DB에 저장하고 보상을 지급한다.
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    c.execute('INSERT INTO expenses (username, date, item, price, category, type) VALUES (?, ?, ?, ?, ?, ?)',
              (username, str(date), item, price, category, type_val))
    conn.commit()
    conn.close()
    update_user_activity(username, xp_gain=10, points_gain=10) # 활동 업데이트

def get_expenses_db(username):
    # 사용자의 모든 소비 기록을 최신순으로 가져와 시각화(Tab 1) 및 AI 분석(Tab 2)에 사용한다.
    conn = sqlite3.connect('money_manager.db')
    df = pd.read_sql_query("SELECT * FROM expenses WHERE username = ? ORDER BY date DESC", conn, params=(username,))
    conn.close()
    return df

def add_wishlist_db(username, item_name, target_price, image_data):
    # '내 꿈 저금통(Tab 4)'에 목표 물건을 저장한다. (단순화를 위해 기존 목표 덮어쓰기를 한다.)
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    # 목표는 하나만 설정 가능하도록 기존 목표 삭제 (심플 버전)
    c.execute('DELETE FROM wishlist WHERE username = ?', (username,))
    c.execute('INSERT INTO wishlist (username, item_name, target_price, image_data) VALUES (?, ?, ?, ?)',
              (username, item_name, target_price, image_data))
    conn.commit()
    conn.close()

def get_wishlist_db(username):
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    c.execute('SELECT * FROM wishlist WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result

# 앱 시작 시 DB 초기화
init_db()

# 페이지 기본 설정
# 브라우저 탭 이름과 아이콘을 설정하고, 레이아웃을 넓게(wide) 사용하여 시각화 효과를 높인다.
st.set_page_config(
    page_title="Money Manager",
    page_icon="💰",
    layout="wide"
)

# --- 사이드바: 테마 설정 ---
# 딱딱한 기본 UI 대신, 학생들에게 친숙한 'Jua' 폰트와 둥근 모서리 디자인을 적용한다.
# 사용자가 선택한 테마 색상이 버튼과 입력창에 실시간으로 반영되어 앱에 애착을 갖게 한다. 
with st.sidebar:
    st.header("🎨 디자인 설정")
    st.write("나만의 테마 색깔을 골라보세요!")
    theme_color = st.color_picker("메인 테마 색상", "#FFC0CB") # 기본값: 파스텔 핑크

# --- 커스텀 CSS 및 폰트 설정 (동적 테마 적용) ---
st.markdown(f"""
    <style>
    /* 구글 폰트 'Jua' 불러오기 */
    @import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');

    /* 전체 폰트 적용 */
    html, body, [class*="css"] {{
        font-family: 'Jua', sans-serif;
    }}

    /* 배경색: 따뜻한 크림색 */
    .stApp {{
        background-color: #F8F0FC; /* 파스텔 퍼플 배경 */
    }}

    /* 버튼 디자인: 둥글고 입체적인 사탕 느낌 */
    .stButton > button {{
        background-color: {theme_color};
        color: white;
        border-radius: 25px;
        border: none;
        padding: 10px 24px;
        font-size: 18px;
        box-shadow: 0 4px 0 rgba(0,0,0,0.1);
        transition: all 0.2s;
    }}
    .stButton > button:hover {{
        filter: brightness(90%);
        transform: scale(1.05); /* 살짝 커짐 */
        color: white;
    }}
    .stButton > button:active {{
        box-shadow: none;
        transform: translateY(4px); /* 눌리는 효과 */
    }}

    /* 입력창 둥글게 */
    .stTextInput > div > div > input, .stNumberInput > div > div > input {{
        border-radius: 15px;
        border: 2px solid {theme_color};
    }}
    
    /* 탭 디자인 */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: #E1F5FE;
        border-radius: 15px 15px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {theme_color};
        color: white !important;
        font-weight: bold;
    }}

    /* 말풍선 스타일 정의 */
    .chat-container {{
        display: flex;
        align-items: flex-start;
        margin-bottom: 15px;
    }}
    .ai-bubble {{
        background-color: {theme_color};
        color: #333333;
        padding: 15px;
        border-radius: 0 20px 20px 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        margin-left: 10px;
        font-size: 18px;
    }}

    /* 랭킹 카드 스타일 */
    .rank-card {{
        background-color: white;
        border-radius: 20px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        display: flex;
        align-items: center;
        border: 2px solid #E6E6FA;
    }}
    .rank-num {{
        font-size: 24px;
        font-weight: bold;
        margin-right: 15px;
        width: 40px;
        text-align: center;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 로그인 화면 로직 ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
# 보안 및 데이터 프라이버시를 위해 세션 상태를 확인하여 비로그인 사용자의 접근을 차단한다. 
if not st.session_state.logged_in:
    st.title("🔐 머니 매니저 로그인")
    st.markdown("### 내 용돈 기입장을 열어볼까요?")
    
    with st.form("login_form"):
        username = st.text_input("닉네임 (이름)", placeholder="예: 짱구")
        pin = st.text_input("비밀번호 (숫자 4자리)", type="password", max_chars=4, placeholder="예: 1234")
        submit_login = st.form_submit_button("시작하기 🚀")
        
        if submit_login:
            if username and len(pin) == 4:
                success, msg = login_user(username, pin)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("닉네임과 4자리 비밀번호를 정확히 입력해주세요!")
    st.stop() # 로그인 전에는 아래 내용 숨김

# 앱 제목 및 소개
st.title("💰 머니 매니저 (Money Manager)")
st.markdown(f"### 🛒 **{st.session_state.username}** 친구의 똑똑한 용돈 관리")

# --- 게이미피케이션 정보 (사이드바/상단) ---
streak_days, user_xp, user_points = get_user_stats(st.session_state.username)
user_level = (user_xp // 100) + 1 # 100XP 마다 레벨업
next_level_xp = 100 - (user_xp % 100)

# 1. 내 캐릭터 키우기 (성장 시스템)
# 사용자의 레벨(XP)에 따라 캐릭터가 알->병아리->닭으로 진화하는 모습을 보여준다.
# '키우기 게임' 요소를 통해 학생들이 앱을 지속적으로 사용하도록 동기를 부여한다.
if user_level < 3:
    char_icon = "🥚"
    level_title = "아직은 알"
    char_desc = "세상에 나올 준비 중이에요!"
elif user_level < 7:
    char_icon = ""
    level_title = "귀여운 병아리"
    char_desc = "삐약삐약! 이제 막 돈 관리를 시작했어요!"
elif user_level < 10:
    char_icon = "🐓"
    level_title = "씩씩한 닭"
    char_desc = "꼬끼오! 스스로 용돈을 관리할 수 있어요!"
else:
    char_icon = "👑"
    level_title = "황금 닭"
    char_desc = "대단해요! 당신은 용돈 관리의 마스터!"

col_info, col_logout = st.columns([4, 1])
with col_info:
    st.info(f"안녕? 난 너의 AI 코치야! 🤖\n오늘도 기록하러 왔구나! 참 잘했어!")
with col_logout:
    if st.button("로그아웃 👋"):
        st.session_state.logged_in = False
        st.rerun()

# 사이드바: 캐릭터 및 성장 정보 표시
with st.sidebar:
    st.divider()
    st.markdown(f"<div style='text-align:center; font-size: 80px;'>{char_icon}</div>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center;'>Lv.{user_level} {level_title}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:gray;'>{char_desc}</p>", unsafe_allow_html=True)
    
    st.write("---")
    st.write(f"**✨ 경험치 (XP):** {user_xp}")
    # 예쁜 프로그레스 바
    st.markdown(f"""
    <div style="background-color: #E0E0E0; border-radius: 10px; height: 15px; width: 100%;">
        <div style="background-color: #FFC0CB; width: {(user_xp % 100)}%; height: 100%; border-radius: 10px;"></div>
    </div>
    <p style="text-align: right; font-size: 12px; color: gray;">다음 레벨까지 {next_level_xp} XP</p>
    """, unsafe_allow_html=True)
    
    st.write(f"**💰 절약 포인트:** {user_points} P")

# 탭 구성
# [목적] 6가지 핵심 활동(기록, 분석, 게임, 목표, 보상, 랭킹)을 탭으로 분리하여 학습 흐름을 체계화한다.
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 마이 데이터 보드", "🤖 AI 머니 코치", "⚖️ 소비 밸런스 게임", "🎋 내 꿈 저금통", "🏆 나의 트로피", "👑 랭킹"])

# --- Tab 1: 마이 데이터 보드 ---
with tab1:
    st.subheader("📝 용돈기입장")
    
    # 입력 폼
    # 학생이 스스로 Need(필요)와 Want(욕구)를 판단하여 입력하게 함으로써 메타인지 능력을 기른다.
    with st.form("input_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("날짜", datetime.now())
            item = st.text_input("내용", placeholder="예: 떡볶이, 용돈")
            price = st.number_input("금액 (원)", min_value=0, step=100, format="%d")
        with col2:
            category = st.selectbox("어떤 종류인가요?", ["간식 🍪", "학용품 ✏️", "장난감 🤖", "교통비 🚌", "기타 🎸"])
            is_need = st.radio("꼭 필요한 것이었나요?", ["필요해요 (Need) ✅", "원해요 (Want) 💖"], horizontal=True)
            
        submitted = st.form_submit_button("기록하기 💾")
        
        if submitted:
            if item and price > 0:
                add_expense_db(st.session_state.username, date, item, price, category, is_need)
                st.balloons()
                st.success(f"💸 '{item}' 소비 기록 완료! 경험치 +10, 포인트 +10 획득! ✨")
            else:
                st.error("앗! 내용과 금액을 정확히 알려주세요. 🥺")

    st.divider()

    # 데이터 시각화 및 표
    df_expense = get_expenses_db(st.session_state.username)
    
    # 1. 컬럼 이름 확인 및 강제 통일
    column_map = {
        'price': '금액', 'amount': '금액', 'cost': '금액',
        'category': '종류', 
        'type': '유형',
        'item': '내용', 'date': '날짜'
    }
    df_expense = df_expense.rename(columns=column_map)
    
    # 2. 빈 데이터 방어 로직
    if not df_expense.empty:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("#### 🍩 어디에 돈을 많이 썼을까?")
            # Plotly 도넛 차트를 통해 어떤 종류(간식 등)에 돈이 편중되었는지 직관적으로 보여준다.
            fig1 = px.pie(df_expense, values="금액", names="종류", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_chart2:
            st.markdown("#### 📊 꼭 필요한 소비였을까?")
            # Plotly 막대 차트를 통해 Need와 Want의 비율을 한눈에 비교하여 합리적 소비 여부를 진단한다.
            fig2 = px.bar(df_expense, x="유형", y="금액", color="유형", text_auto=True, color_discrete_map={"필요해요 (Need) ✅": "#4CAF50", "원해요 (Want) 💖": "#FF9800"})
            st.plotly_chart(fig2, use_container_width=True)
            
        st.markdown("#### 📋 지출 내역")
        st.dataframe(df_expense[['날짜', '내용', '금액', '종류', '유형']], use_container_width=True)
    else:
        st.info("아직 지출 기록이 없어요! 첫 기록을 남겨보세요. 🎈")
        
    # --- 월간 캘린더 리포트 ---
    st.write("---")
    st.subheader("📅 월간 캘린더 리포트")
    
    # 날짜 선택
    now = datetime.now()
    col_y, col_m = st.columns(2)
    with col_y:
        year = st.selectbox("연도", range(now.year - 1, now.year + 2), index=1, key="cal_year")
    with col_m:
        month = st.selectbox("월", range(1, 13), index=now.month - 1, key="cal_month")

    # 데이터 필터링
    if not df_expense.empty:
        df_expense['날짜'] = pd.to_datetime(df_expense['날짜'])
        df_month_exp = df_expense[(df_expense['날짜'].dt.year == year) & (df_expense['날짜'].dt.month == month)]
    else:
        df_month_exp = pd.DataFrame()

    # 3. 무지출 챌린지 연속 기록 계산 (간단 버전)
    # 현재 달의 1일부터 오늘까지 지출 없는 날 계산한다.
    # 최근 지출 없는 날(No Spend Days)을 계산하여 절약 습관을 칭찬한다.
    no_spend_streak = 0
    today_date = datetime.now().date()
    check_date = today_date
    
    # 최근 30일간 기록 확인
    while True:
        # 해당 날짜에 지출이 있는지 확인
        day_spent = 0
        if not df_expense.empty:
            day_spent = df_expense[df_expense['날짜'].dt.date == check_date]['금액'].sum()
        
        if day_spent == 0:
            no_spend_streak += 1
            check_date -= timedelta(days=1)
            if no_spend_streak > 30: break # 최대 30일까지만 체크
        else:
            break

    # 캘린더 스타일
    st.markdown("""
    <style>
    .day-box {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 5px;
        height: 80px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        font-size: 14px;
        border: 2px solid #F0F0F0;
    }
    .day-num { font-weight: bold; color: #555; margin-bottom: 2px; }
    .expense-text { color: #FF6B6B; font-weight: bold; font-size: 12px; }
    .good-job { font-size: 24px; margin-top: 5px; }
    .streak-banner { background-color: #E6E6FA; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px; color: #6A5ACD; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    if no_spend_streak > 0:
        st.markdown(f"<div class='streak-banner'>🔥 현재 {no_spend_streak}일째 무지출 성공 중! 대단해요!</div>", unsafe_allow_html=True)

    # 요일 헤더
    cols = st.columns(7)
    days_list = ["월", "화", "수", "목", "금", "토", "일"]
    for i, day in enumerate(days_list):
        cols[i].markdown(f"<div style='text-align: center; font-weight: bold; color: #555;'>{day}</div>", unsafe_allow_html=True)

    # 달력 그리기
    # HTML/CSS를 활용해 소비가 있는 날은 금액을, 없는 날은 '돼지 아이콘'을 표시하여 소비 패턴을 시각화한다.
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("<div class='day-box' style='background-color: transparent; border: none; box-shadow: none;'></div>", unsafe_allow_html=True)
                else:
                    current_date = datetime(year, month, day).date()
                    daily_spent = 0
                    if not df_month_exp.empty:
                        daily_spent = df_month_exp[df_month_exp['날짜'].dt.date == current_date]['금액'].sum()
                    
                    content = f"<div class='day-num'>{day}</div>"
                    if daily_spent > 0:
                        content += f"<div class='expense-text'>💸 -{daily_spent:,}</div>"
                    elif current_date <= datetime.now().date():
                        content += "<div class='good-job'>🐷</div>" # 무지출 도장
                    st.markdown(f"<div class='day-box'>{content}</div>", unsafe_allow_html=True)

    # 월말 결산 및 AI 분석
    st.markdown("### 📊 이번 달 결산")
    total_exp_month = df_month_exp['금액'].sum() if not df_month_exp.empty else 0
    
    st.metric("총 지출", f"{total_exp_month:,}원")

    st.info(f"💡 **AI 코치의 {month}월 분석:**")
    # 지난달 비교 로직
    prev_date = datetime(year, month, 1) - timedelta(days=1)
    prev_exp = 0
    if not df_expense.empty:
        prev_exp = df_expense[(df_expense['날짜'].dt.year == prev_date.year) & (df_expense['날짜'].dt.month == prev_date.month)]['금액'].sum()
    
    if prev_exp > 0:
        diff = total_exp_month - prev_exp
        if diff < 0:
            st.write(f"와우! 지난달보다 **{abs(diff):,}원**이나 적게 썼어요! 알뜰살뜰 멋져요! 👏")
        elif diff > 0:
            st.write(f"지난달보다 **{diff:,}원** 더 썼네요. 다음 달엔 조금 더 아껴볼까요? 화이팅! 💪")
        else:
            st.write("지난달이랑 똑같이 썼네요! 꾸준함이 대단해요!")
    else:
        st.write("지난달 기록이 없어서 비교할 수 없지만, 이번 달도 참 잘했어요!")

# --- Tab 2: AI 머니 코치 ---
with tab2:
    st.subheader("🤖 AI 머니 코치")
    df = get_expenses_db(st.session_state.username)
    
    if df.empty:
        st.warning("아직 기록이 없어서 분석할 수 없어요. 🥺 '마이 데이터 보드'에 먼저 기록해주세요!")
    else:
        st.write("친구의 소비 습관을 보고 내가 칭찬이나 조언을 해줄게!")
        if st.button("AI 코치님, 분석해주세요! 🔍"):
            
            # 컬럼 이름 통일 (Tab 1과 동일하게)
            df = df.rename(columns={'price': '금액', 'category': '종류', 'type': '유형', 'item': '내용', 'date': '날짜'})
            
            # 데이터 계산
            total_spent = df['금액'].sum()
            snack_spent = df[df['종류'] == '간식']['금액'].sum()
            snack_ratio = (snack_spent / total_spent * 100) if total_spent > 0 else 0
            
            wants_amount = df[df['유형'] == '원해요 (Want) 💖']['금액'].sum()
            needs_amount = df[df['유형'] == '필요해요 (Need) ✅']['금액'].sum()

            st.markdown(f"### 📊 분석 결과 (총 소비: {total_spent:,}원)")
            # Rule-based 알고리즘을 사용해 간식비 40% 초과 등 특정 조건 만족 시 맞춤형 피드백을 제공한다.
            # 초등학생이 이해하기 쉽도록 색상 카드(초록/빨강)와 아이콘으로 즉각적인 피드백을 준다.

            # Rule 1: 간식 비율 체크
            if snack_ratio > 40:
                st.warning(f"🍪 **간식 경보!** 간식비가 전체의 {snack_ratio:.1f}%를 차지해요. 군것질 비율이 너무 높아요! 건강과 지갑을 위해 조금만 줄여볼까요?")
            else:
                st.success(f"🍎 **아주 좋아요!** 간식비 비율이 {snack_ratio:.1f}%로 적절해요.")

            # Rule 2: Needs vs Wants 체크
            if wants_amount > needs_amount:
                st.error("💸 **지출 주의!** '원해요(Want)'에 쓴 돈이 '필요해요(Need)'보다 많아요. 꼭 필요하지 않은 물건을 너무 많이 샀어요. 신중한 선택이 필요해요!")
            else:
                st.success("⚖️ **훌륭해요!** 꼭 필요한 곳에 돈을 잘 쓰고 있군요. 합리적인 소비 습관입니다!")

# --- Tab 3: 소비 밸런스 게임 ---
with tab3:
    st.subheader("⚖️ 소비 밸런스 게임")
    st.write("현명한 선택을 하는 연습을 해봅시다!")
    # 학생들의 흥미를 끌 수 있는 딜레마 시나리오를 정의한다.
    # 시나리오 리스트 정의
    scenarios = [
        {
            "id": "A",
            "situation": "용돈을 2주 동안 모았어요!",
            "choice_a": "👟 내가 정말 갖고 싶었던 한정판 운동화 사기",
            "choice_b": "🎁 곧 다가오는 엄마 생신 선물 사기 + 남은 돈 저축",
            "result_a": "👟 **선택 결과:** 드디어 꿈에 그리던 운동화를 가졌어요! 친구들이 부러워하겠네요. 하지만 엄마 선물은... 정성 담긴 편지로 대신해야 할까요? (기회비용: 엄마의 감동, 저축)",
            "result_b": "🎁 **선택 결과:** 엄마가 선물을 받고 정말 기뻐하실 거예요! 남은 돈도 저축했으니 뿌듯하네요. 운동화는 나중에 또 기회가 있겠죠? (기회비용: 한정판 운동화)"
        },
        {
            "id": "B",
            "situation": "배가 너무 고픈 하교 시간!",
            "choice_a": "🌭 지금 당장 편의점에서 컵라면과 간식 사 먹기",
            "choice_b": "🚲 꾹 참고 집에 가서 밥 먹고, 돈 모아서 자전거 사기",
            "result_a": "🌭 **선택 결과:** 배고픔 해결! 당장은 행복하지만, 자전거를 사려면 돈을 다시 처음부터 모아야 해요. (기회비용: 자전거 살 돈)",
            "result_b": "🚲 **선택 결과:** 꼬르륵 소리는 났지만, 자전거 목표에 한 걸음 더 다가갔어요! 집밥도 맛있게 먹었답니다. (기회비용: 지금 당장의 포만감)"
        },
        {
            "id": "C",
            "situation": "새 학기 학용품을 사야 해요.",
            "choice_a": "✨ 친구들이 다 쓰는 비싸고 예쁜 '인싸' 필통",
            "choice_b": "✏️ 튼튼하고 실용적인 필통 + 남는 돈으로 좋아하는 책 사기",
            "result_a": "✨ **선택 결과:** 예쁜 필통 덕분에 공부할 맛이 나네요! 하지만 읽고 싶었던 책은 도서관에서 빌려봐야겠어요. (기회비용: 책 소장, 여유 자금)",
            "result_b": "✏️ **선택 결과:** 실속 있는 소비를 했네요! 튼튼한 필통도 생기고, 재미있는 책도 읽을 수 있어요. (기회비용: 유행을 따르는 즐거움)"
        }
    ]

    # 게임 상태 초기화 (시나리오가 없거나, 초기화 필요 시)
    if "current_scenario" not in st.session_state:
        st.session_state.current_scenario = random.choice(scenarios)
        st.session_state.game_choice = None

    scenario = st.session_state.current_scenario

    st.markdown("""
    <div style="background-color:#FFF9C4; padding:15px; border-radius:15px; border:2px dashed #FBC02D;">
        <strong>🤔 오늘의 고민 상황:</strong><br>
        {scenario['situation']}<br>
        둘 중 <strong>하나만</strong> 선택해야 해!
    </div>
    <br>
    """, unsafe_allow_html=True)
    
    col_choice1, col_choice2 = st.columns(2)
    
    with col_choice1:
        if st.button(scenario['choice_a']):
            st.session_state.game_choice = "A"
    with col_choice2:
        if st.button(scenario['choice_b']):
            st.session_state.game_choice = "B"
            
    if st.session_state.game_choice:
        st.info("선택 완료! 아래에 이유를 적어주세요 👇")
        st.divider()
        
        # 결과 말풍선 표시 함수
        def show_game_result(emoji, text):
            st.markdown(f"""
            <div class="chat-container">
                <div style="font-size: 40px;">{emoji}</div>
                <div class="ai-bubble">{text}</div>
            </div>
            """, unsafe_allow_html=True)

        if st.session_state.game_choice == "A":
            show_game_result("🅰️", scenario['result_a'])
        else:
            show_game_result("🅱️", scenario['result_b'])
            
        st.markdown("#### 📝 왜 그런 선택을 했니?")
        # 학생이 선택에 대한 이유와 기회비용을 직접 글로 적어보게 하여 의사결정 과정을 내면화한다.
        reason = st.text_area("이 선택을 하면 **가장 좋은 점**은 무엇인가요? 반대로 이 선택 때문에 **포기해야 하는 것(기회비용)**은 무엇인지 구체적으로 적어보세요.", placeholder="예: 가장 좋은 점은 ... 하지만 ...을 포기해야 해요.")
        
        if reason:
            st.balloons()
            st.success("🎉 **미션 완료!** 자신의 생각을 멋지게 설명했네! 참 잘했어! 💯")
            if st.button("다른 문제 풀기 🔄"):
                del st.session_state.current_scenario
                st.session_state.game_choice = None
                st.rerun()

# --- Tab 4: 내 꿈 저금통 ---
with tab4:
    st.subheader("🎋 내 꿈 저금통 (Wish List)")
    
    st.write("갖고 싶은 물건을 등록하고 목표를 세워보세요!")
    
    # 목표 가져오기
    wish = get_wishlist_db(st.session_state.username)

    # 위시리스트가 있으면 목표 카드(이미지, 가격)를 보여주어 '자원의 희소성'을 시각화한다.
    if wish:
        # 목표가 있을 때
        item_name = wish[2]
        target_price = wish[3]
        image_data = wish[4]
        
        col_goal1, col_goal2 = st.columns([1, 2])
        with col_goal1:
            if image_data:
                st.image(image_data, caption=item_name, use_container_width=True)
            else:
                st.markdown(f"<div style='font-size:100px; text-align:center;'>🎁</div>", unsafe_allow_html=True)
        
        with col_goal2:
            st.markdown(f"### 🎯 목표: {item_name}")
            st.markdown(f"#### 필요 금액: {target_price:,}원")
            
            st.info("열심히 절약해서 목표를 달성해보세요! 화이팅! 💪")
                
            if st.button("목표 수정/삭제하기 🗑️"):
                add_wishlist_db(st.session_state.username, "", 0, None) # 삭제 처리
                st.rerun()
    else:
        # 목표가 없을 때 입력 폼
        st.write("갖고 싶은 물건이 있나요? 목표를 세워보세요!")
        with st.form("wishlist_form"):
            w_item = st.text_input("갖고 싶은 물건 이름")
            w_price = st.number_input("얼마가 필요한가요?", min_value=0, step=1000)
            w_img = st.file_uploader("사진이 있다면 올려주세요 (선택)", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("목표 설정하기 ✨"):
                if w_item and w_price > 0:
                    img_bytes = w_img.getvalue() if w_img else None
                    add_wishlist_db(st.session_state.username, w_item, w_price, img_bytes)
                    st.success("목표가 설정되었어요! 화이팅!")
                    st.rerun()
                else:
                    st.error("물건 이름과 가격을 입력해주세요.")

# --- Tab 5: 나의 트로피 ---
with tab5:
    st.subheader("🏆 나의 트로피 (명예의 전당)")
    st.write("열심히 활동해서 멋진 배지를 모아보세요!")
    
    # 배지 획득 조건 체크
    # 사용자 데이터(Streak, XP)를 확인하여 특정 조건 달성 시 배지를 해제한다.
    badges = []
    
    # 1. 기록왕 (7일 연속)
    if streak_days >= 7:
        badges.append({"icon": "👑", "name": "기록왕", "desc": "7일 연속 기록 달성!"})
    else:
        badges.append({"icon": "🔒", "name": "기록왕 (잠김)", "desc": "7일 연속 기록하면 열려요!"})
        
    # 2. 절약왕 (포인트 100점 이상)
    if user_points >= 100:
        badges.append({"icon": "🐷", "name": "절약왕", "desc": "절약 포인트 100점 달성!"})
    else:
        badges.append({"icon": "🔒", "name": "절약왕 (잠김)", "desc": "포인트 100점을 모으면 열려요!"})

    # 3. 레벨업 마스터 (Lv.5 달성)
    if user_level >= 5:
        badges.append({"icon": "🎓", "name": "척척박사", "desc": "레벨 5 달성!"})
    else:
        badges.append({"icon": "🔒", "name": "척척박사 (잠김)", "desc": "레벨 5가 되면 열려요!"})

    # 배지 표시
    cols = st.columns(3)
    for i, badge in enumerate(badges):
        with cols[i]:
            st.markdown(f"""
            <div style="background-color: white; padding: 20px; border-radius: 15px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                <div style="font-size: 50px;">{badge['icon']}</div>
                <h4 style="margin: 10px 0;">{badge['name']}</h4>
                <p style="color: gray; font-size: 14px;">{badge['desc']}</p>
            </div>
            """, unsafe_allow_html=True)

# --- Tab 6: 랭킹 (명예의 전당) ---
with tab6:
    st.subheader("🏆 우리 반 명예의 전당")
    st.write("누가누가 절약 포인트를 많이 모았을까요?")
    
    leaderboard_df = get_leaderboard()
    
    if not leaderboard_df.empty:
        # 포인트가 높은 상위 친구들의 명단을 카드로 보여주어 건전한 경쟁과 사회적 학습을 유도한다.
        for index, row in leaderboard_df.iterrows():
            rank = index + 1
            r_username = row['username']
            r_points = row['points']
            r_xp = row['xp']
            r_level = (r_xp // 100) + 1
            
            # 메달 아이콘
            if rank == 1: medal = "🥇"
            elif rank == 2: medal = "🥈"
            elif rank == 3: medal = "🥉"
            else: medal = str(rank)
            
            st.markdown(f"""
            <div class="rank-card">
                <div class="rank-num">{medal}</div>
                <div style="flex-grow: 1;">
                    <div style="font-size: 18px; font-weight: bold;">{r_username} <span style="font-size:14px; color:gray;">(Lv.{r_level})</span></div>
                </div>
                <div style="font-weight: bold; color: #FF69B4;">{r_points} P</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("아직 랭킹 데이터가 없어요. 친구들을 초대해보세요!")
