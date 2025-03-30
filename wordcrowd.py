import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import os
import base64
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from textblob import TextBlob

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
        """

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

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

def student_view():
    apply_custom_css()
    query_params = st.query_params
    topic = query_params.get("topic", "")

    if not topic:
        st.error("❗ URL에 주제 정보가 없습니다.")
        return

    # 모바일 대응 줄바꿈용 span 태그 포함
    st.markdown(
        f'<h1 class="section-title">📥 <span class="mobile-wrap">[{topic}]<br>피드백 제출</span></h1>',
        unsafe_allow_html=True
    )

    with st.form("feedback_form"):
        feedback = st.text_input("50자 이내로 피드백을 입력해주세요")
        submitted = st.form_submit_button("제출")
        if submitted:
            if feedback and len(feedback) <= 50:
                save_feedback(topic, feedback)
                st.success("제출되었습니다!")
            else:
                st.error("50자 이내로 작성해주세요.")

def get_sentiment_class(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return "feedback-card-positive"
    elif polarity < -0.1:
        return "feedback-card-negative"
    else:
        return "feedback-card"

def teacher_view():
    apply_custom_css()
    st_autorefresh(interval=5000, key="refresh")

    st.markdown('<h1 class="section-title">📋 주제별 피드백 보기</h1>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("<div class='sidebar-section'><h2>📝 새 주제 추가</h2></div>", unsafe_allow_html=True)
        new_topic = st.text_input("새 주제를 입력하세요")
        if st.button("주제 추가"):
            if new_topic.strip():
                add_topic(new_topic.strip())
                st.success(f"'{new_topic}' 주제가 추가되었습니다.")
                st.experimental_rerun()

    topics = load_topics()
    if not topics:
        st.info("아직 주제가 없습니다.")
        return

    base_url = get_base_url()
    with st.sidebar:
        st.markdown("<h2 class='sidebar-section'>📸 주제별 QR 코드</h2>", unsafe_allow_html=True)
        for topic in topics:
            student_url = f"{base_url}/?mode=student&topic={topic}"
            qr = qrcode.make(student_url)
            buffered = BytesIO()
            qr.save(buffered, format="PNG")
            st.markdown(f"**📌 {topic}**")
            st.image(buffered.getvalue(), caption=student_url, use_container_width=True)
            st.markdown("<hr>", unsafe_allow_html=True)

    for topic in topics:
        df = load_feedback(topic)
        count = len(df)

        st.markdown(
            f'<h2 class="topic-header">📌 주제: {topic} ({count}건 제출됨)</h2>',
            unsafe_allow_html=True
        )

        if df.empty:
            st.info("❗ 아직 피드백이 없습니다.")
        else:
            df = df.sort_values(by="timestamp", ascending=True)

            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="⬇️ CSV 다운로드",
                data=csv,
                file_name=f"feedback_{topic}.csv",
                mime="text/csv"
            )

            for i, row in enumerate(df.itertuples(), 1):
                sentiment_class = get_sentiment_class(row.feedback)
                st.markdown(
                    f'''<div class="{sentiment_class}">
                        <strong>{i}.</strong><br>
                        {row.feedback}
                    </div>''',
                    unsafe_allow_html=True
                )
        st.markdown("<hr>", unsafe_allow_html=True)

def main():
    query_params = st.query_params
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
import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import os
import base64
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from textblob import TextBlob

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
        """

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

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

def student_view():
    apply_custom_css()
    query_params = st.query_params
    topic = query_params.get("topic", "")

    if not topic:
        st.error("❗ URL에 주제 정보가 없습니다.")
        return

    st.markdown(
        f'<h1 class="section-title">📥 [{topic}] 피드백 제출</h1>',
        unsafe_allow_html=True
    )

    with st.form("feedback_form"):
        feedback = st.text_input("50자 이내로 피드백을 입력해주세요")
        submitted = st.form_submit_button("제출")
        if submitted:
            if feedback and len(feedback) <= 50:
                save_feedback(topic, feedback)
                st.success("제출되었습니다!")
            else:
                st.error("50자 이내로 작성해주세요.")

def get_sentiment_class(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return "feedback-card-positive"
    elif polarity < -0.1:
        return "feedback-card-negative"
    else:
        return "feedback-card"

def teacher_view():
    apply_custom_css()
    st_autorefresh(interval=5000, key="refresh")

    st.markdown('<h1 class="section-title">📋 주제별 피드백 보기</h1>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("<div class='sidebar-section'><h2>📝 새 주제 추가</h2></div>", unsafe_allow_html=True)
        new_topic = st.text_input("새 주제를 입력하세요")
        if st.button("주제 추가"):
            if new_topic.strip():
                add_topic(new_topic.strip())
                st.success(f"'{new_topic}' 주제가 추가되었습니다.")
                st.experimental_rerun()

    topics = load_topics()
    if not topics:
        st.info("아직 주제가 없습니다.")
        return

    base_url = get_base_url()
    with st.sidebar:
        st.markdown("<h2 class='sidebar-section'>📸 주제별 QR 코드</h2>", unsafe_allow_html=True)
        for topic in topics:
            student_url = f"{base_url}/?mode=student&topic={topic}"
            qr = qrcode.make(student_url)
            buffered = BytesIO()
            qr.save(buffered, format="PNG")
            st.markdown(f"**📌 {topic}**")
            st.image(buffered.getvalue(), caption=student_url, use_container_width=True)
            st.markdown("<hr>", unsafe_allow_html=True)

    for topic in topics:
        df = load_feedback(topic)
        count = len(df)

        st.markdown(
            f'<h2 class="topic-header">📌 주제: {topic} ({count}건 제출됨)</h2>',
            unsafe_allow_html=True
        )

        if df.empty:
            st.info("❗ 아직 피드백이 없습니다.")
        else:
            df = df.sort_values(by="timestamp", ascending=True)

            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="⬇️ CSV 다운로드",
                data=csv,
                file_name=f"feedback_{topic}.csv",
                mime="text/csv"
            )

            for i, row in enumerate(df.itertuples(), 1):
                sentiment_class = get_sentiment_class(row.feedback)
                st.markdown(
                    f'''<div class="{sentiment_class}">
                        <strong>{i}.</strong><br>
                        {row.feedback}
                    </div>''',
                    unsafe_allow_html=True
                )
        st.markdown("<hr>", unsafe_allow_html=True)

def main():
    query_params = st.query_params
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
