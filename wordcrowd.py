import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import socket
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

TOPICS_FILE = "topics.txt"

# 내부 IP 가져오기
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# 피드백 파일 경로
def get_feedback_file(topic):
    return f"feedback_{topic}.csv"

# 주제 목록 불러오기
def load_topics():
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]
    return []

# 주제 추가
def add_topic(topic):
    topics = load_topics()
    if topic and topic not in topics:
        topics.append(topic)
        with open(TOPICS_FILE, 'w', encoding='utf-8') as f:
            for t in topics:
                f.write(f"{t}\n")

# 피드백 저장
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

# 피드백 로딩
def load_feedback(topic):
    filename = get_feedback_file(topic)
    if os.path.exists(filename):
        return pd.read_csv(filename)
    else:
        return pd.DataFrame(columns=["timestamp", "feedback"])

# 학생 화면
def student_view():
    query_params = st.experimental_get_query_params()
    topic = query_params.get("topic", [""])[0]

    if not topic:
        st.error("❗ URL에 주제 정보가 없습니다.")
        return

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

# 강사 화면
def teacher_view():
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

    local_ip = get_local_ip()

    st.sidebar.subheader("📸 주제별 QR 코드")

    # 주제별 QR 생성
    for topic in topics:
        student_url = f"http://{local_ip}:8501/?mode=student&topic={topic}"
        qr = qrcode.make(student_url)
        buffered = BytesIO()
        qr.save(buffered, format="PNG")
        st.sidebar.markdown(f"**📌 {topic}**")
        st.sidebar.image(buffered.getvalue(), caption=student_url, use_column_width=True)
        st.sidebar.markdown("---")

    # 본문에 주제별 피드백 출력
    for topic in topics:
        df = load_feedback(topic)
        count = len(df)
        st.markdown(f"### 📌 주제: {topic} ({count}건 제출됨)")

        if df.empty:
            st.write("❗ 아직 피드백이 없습니다.")
        else:
            df = df.sort_values(by="timestamp", ascending=True)
            for idx, row in df.iterrows():
                st.markdown(f"**[{row['timestamp']}]** {row['feedback']}")
        st.markdown("---")

def main():
    query_params = st.experimental_get_query_params()
    mode = query_params.get("mode", ["teacher"])[0]

    if mode == "student":
        student_view()
    else:
        teacher_view()

if __name__ == "__main__":
    main()
