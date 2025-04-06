import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import os
import base64
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from textblob import TextBlob
from sentiment_words import positive_words, negative_words
import urllib.parse

TOPICS_FILE = "topics.txt"

def get_base_url():
    return "https://feedback-nppwjkm3csgjpf3peanwvq.streamlit.app"

def reset_all_data():
    if os.path.exists(TOPICS_FILE):
        os.remove(TOPICS_FILE)
    for f in os.listdir():
        if f.startswith("feedback_") and f.endswith(".csv"):
            os.remove(f)

def apply_custom_css():
    css = ""
    with open("style.css") as f:
        css += f.read()

    with open("akokonut.ttf", "rb") as font_file:
        font_encoded = base64.b64encode(font_file.read()).decode()
        css += f"""
        @font-face {{
            font-family: "MyFont";
            src: url(data:font/ttf;base64,{font_encoded}) format("truetype");
        }}

        section[data-testid="stSidebar"] {{
            min-width: 400px !important;
            max-width: 450px !important;
        }}

        .sidebar-section img {{
            width: 100% !important;
            max-width: 360px !important;
            margin-bottom: 10px;
        }}

        .section-title {{
            margin-left: -100px !important;
        }}

        .feedback-card {{
            background-color: #e0e0e0 !important;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
        }}

        .feedback-card-positive {{
            background-color: #ffe6ea !important;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
        }}

        .feedback-card-negative {{
            background-color: #e0f0ff !important;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
        }}
        """

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def normalize_topic(topic):
    return urllib.parse.unquote(topic.strip())

def get_feedback_file(topic):
    topic = normalize_topic(topic)
    return f"feedback_{topic}.csv"

def load_topics():
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]
    return []

def add_topic(topic):
    topic = normalize_topic(topic)
    topics = load_topics()
    if topic and topic not in topics:
        topics.append(topic)
        with open(TOPICS_FILE, 'w', encoding='utf-8') as f:
            for t in topics:
                f.write(f"{t}\n")

def save_feedback(topic, feedback):
    topic = normalize_topic(topic)
    add_topic(topic)
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
    topic = normalize_topic(topic)
    filename = get_feedback_file(topic)
    if os.path.exists(filename):
        return pd.read_csv(filename)
    else:
        return pd.DataFrame(columns=["timestamp", "feedback"])

def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    return buf

def main():
    # URL 쿼리에서 reset 여부 확인
    query_params_raw = st.query_params
    if isinstance(query_params_raw, dict):
        if 'reset' in query_params_raw and query_params_raw['reset'] == 'true':
            reset_all_data()
            st.success("모든 데이터가 초기화되었습니다. 새로 시작할 준비가 되었습니다!")
            return
    apply_custom_css()

    query_params = st.query_params
    mode = query_params.get("mode", "teacher")
    topic = query_params.get("topic")
    if topic:
        topic = normalize_topic(topic)

    if mode == "student" and topic:
        st.title(f"📥 [{topic}] 피드백 제출")
        st.write("50자 이내로 피드백을 입력해주세요")
        feedback = st.text_input("")
        if st.button("제출"):
            if feedback.strip():
                save_feedback(topic, feedback)
                st.success("제출되었습니다!")
    else:
        st.title("📋 주제별 피드백 보기")
        st_autorefresh(interval=5000, key="refresh")

        with st.sidebar:
            st.header("📝 새 주제 추가")
            new_topic = st.text_input("새 주제를 입력하세요")
            if st.button("주제 추가"):
                if new_topic.strip():
                    add_topic(new_topic.strip())
                    st.success(f"주제 '{new_topic}'가 추가되었습니다.")

            st.markdown("## 📸 주제별 QR 코드")
            for t in load_topics():
                st.markdown(f"📌 {t}")
                encoded_topic = urllib.parse.quote(t)
                qr_url = f"{get_base_url()}?mode=student&topic={encoded_topic}"
                buf = generate_qr_code(qr_url)
                st.image(buf)
                st.caption(f"[{qr_url}]({qr_url})")

        topics = load_topics()
        if not topics:
            st.info("아직 등록된 주제가 없습니다.")
        else:
            for t in topics:
                df = load_feedback(t)
                st.subheader(f"📌 주제: {t} ({len(df)}건 제출됨)")

                csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="⬇️ CSV 다운로드",
                    data=csv,
                    file_name=f"feedback_{t}.csv",
                    mime="text/csv"
                )

                if df.empty:
                    st.warning("❗ 아직 피드백이 없습니다.")
                else:
                    for i, row in df.iterrows():
                        sentiment_class = "feedback-card"
                        txt = row["feedback"]
                        if any(word in txt for word in positive_words):
                            sentiment_class = "feedback-card-positive"
                        elif any(word in txt for word in negative_words):
                            sentiment_class = "feedback-card-negative"

                        st.markdown(f"<div class='{sentiment_class}'><strong>{i+1}.</strong> {txt}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
