import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import os
import base64
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

TOPICS_FILE = "topics.txt"

# ✅ Cloud 고정 주소
def get_base_url():
    return "https://feedback-nppwjkm3csgjpf3peanwvq.streamlit.app"

# ✅ 외부 초기화 처리
def reset_all_data():
    if os.path.exists(TOPICS_FILE):
        os.remove(TOPICS_FILE)
    for f in os.listdir():
        if f.startswith("feedback_") and f.endswith(".csv"):
            os.remove(f)

# ✅ 사용자 폰트 적용 함수
def get_font_style():
    with open("a코코넛.ttf", "rb") as f:
        font_data = f.read()
        encoded = base64.b64encode(font_data).decode()
    return f"""
    <style>
    @font-face {{
        font-family: "MyFont";
        src: url(data:font/ttf;base64,{encoded}) format('truetype');
    }}
    html, body, [class*="css"] {{
        font-family: "MyFont", sans-serif;
        font-size: 20px !important;
    }}
    h1, h2, h3 {{
        font-size: 24px !important;
    }}
    </style>
    """

def get_feedback_file(topic):
    return f"feedback_{topic}.csv"

def load_topics():
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]
    return []

def add_topic(topic):
    topics = load_topics()
    if topic and topic not in topics:
        topics.append(topic)
        with open(TOPICS_FILE, 'w', encoding='utf-8') as f:
            for t in topics:
                f.write(f"{t}\n")

def save_feedback(topic, feedback):
    filename = get_feedback_file(topic)
    df = pd.DataFrame({
        "timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "feedback": [feedback]
    })
    if os.path.exists(filename):
        existing = pd.read_csv(filename)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_csv(filename, index=False)

def load_feedback(topic):
    filename = get_feedback_file(topic)
    if os.path.exists(filename):
        return pd.read_csv(filename)
    else:
        return pd.DataFrame(columns=["timestamp", "feedback"])

# ▶️ 학생 화면
def student_view():
    query_params = st.query_params
    topic = query_params.get("topic", "")

    if not topic:
        st.error("❗ URL에 주제 정보가 없습니다.")
        return

    st.markdown(get_font_style(), unsafe_allow_html=True)
    st.title(f"📥 [{topic}] 피드백 제출")

    with st.form("feedback_form"):
        feedback = st.text_input("50자 이내로 피드백을 입력해주세요")
        submitted = st.form_submit_button("제출")
        if submitted:
            if feedback and len(feedback) <= 50:
                save_feedback(topic, feedback)
                st.success("제출되었습니다!")
            else:
                st.error("50자 이내로 작성해주세요.")

# 👨‍🏫 강사 화면
def teacher_view():
    st.markdown(get_font_style(), unsafe_allow_html=True)
    st.title("📋 주제별 피드백 보기")
    st_autorefresh(interval=5000, key="refresh")

    st.sidebar.subheader("📝 새 주제 추가")
    new_topic = st.sidebar.text_input("새 주제를 입력하세요")
    if st.sidebar.button("주제 추가"):
        if new_topic.strip():
            add_topic(new_topic.strip())
            st.success(f"'{new_topic}' 주제가 추가되었습니다.")
            st.experimental_rerun()

    topics = load_topics()
    if not topics:
        st.info("아직 주제가 없습니다.")
        return

    base_url = get_base_url()
    st.sidebar.subheader("📸 주제별 QR 코드")

    for topic in topics:
        student_url = f"{base_url}/?mode=student&topic={topic}"
        qr = qrcode.make(student_url)
        buffered = BytesIO()
        qr.save(buffered, format="PNG")
        st.sidebar.markdown(f"**📌 {topic}**")
        st.sidebar.image(buffered.getvalue(), caption=student_url, use_container_width=True)
        st.sidebar.markdown("---")

    for topic in topics:
        df = load_feedback(topic)
        count = len(df)
        st.markdown(f"### 📌 주제: {topic} ({count}건 제출됨)")

        if df.empty:
            st.write("❗ 아직 피드백이 없습니다.")
        else:
            df = df.sort_values(by="timestamp", ascending=True)

            # ✅ CSV 다운로드 버튼
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="⬇️ CSV 다운로드",
                data=csv,
                file_name=f"feedback_{topic}.csv",
                mime="text/csv"
            )

            for _, row in df.iterrows():
                st.markdown(f"**[{row['timestamp']}]** {row['feedback']}")

        st.markdown("---")

# 🔁 진입점
def main():
    query_params = st.query_params

    # ✅ reset trigger
    if query_params.get("reset", "") == "true":
        reset_all_data()
        st.success("✅ 모든 데이터가 초기화되었습니다.")
        st.stop()

    mode = query_params.get("mode", "teacher")

    if mode == "student":
        student_view()
    else:
        teacher_view()

if __name__ == "__main__":
    main()
