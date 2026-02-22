import streamlit as st
import sqlite3
import pandas as pd
import easyocr
import cv2
import numpy as np
from datetime import datetime

conn = sqlite3.connect('proseka_records.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        play_date TEXT,
        level TEXT,
        song_title TEXT,
        perfect INTEGER,
        great INTEGER,
        good INTEGER,
        bad INTEGER,
        miss INTEGER,
        fast INTEGER,
        late INTEGER
    )
''')
conn.commit()

@st.cache_resource
def load_reader():
    return easyocr.Reader(['ko', 'en'])

reader = load_reader()

def extract_data_from_image(image):
    result = reader.readtext(image, detail=0)
    play_date = datetime.now().strftime("%Y-%m-%d")
    song_title = "Unknown Song"
    if len(result) > 0:
        song_title = str(result[0])
    level = "EXPERT"
    perfect = 0
    great = 0
    good = 0
    bad = 0
    miss = 0
    fast = 0
    late = 0
    return play_date, level, song_title, perfect, great, good, bad, miss, fast, late

tab_upload, tab_view = st.tabs(["기록 업로드", "결과 조회"])

with tab_upload:
    st.write("게임 결과 캡처 사진 업로드")
    uploaded_file = st.file_uploader("이미지 파일을 선택할 것", type=['png', 'jpg', 'jpeg'])
    if uploaded_file is not None:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        st.write("업로드한 게임 결과 사진 확인")
        st.image(image_rgb, use_container_width=True)
        extracted_data = extract_data_from_image(image)
        st.write("추출된 데이터 확인 및 수정 (오류가 있다면 직접 수정할 것)")
        with st.form("verification_form"):
            col1, col2 = st.columns(2)
            with col1:
                edit_play_date = st.text_input("플레이 날짜", value=extracted_data[0])
                edit_level = st.text_input("레벨", value=extracted_data[1])
                edit_song_title = st.text_input("악곡 이름", value=extracted_data[2])
                edit_fast = st.number_input("Fast", value=extracted_data[8], min_value=0)
                edit_late = st.number_input("Late", value=extracted_data[9], min_value=0)
            with col2:
                edit_perfect = st.number_input("Perfect", value=extracted_data[3], min_value=0)
                edit_great = st.number_input("Great", value=extracted_data[4], min_value=0)
                edit_good = st.number_input("Good", value=extracted_data[5], min_value=0)
                edit_bad = st.number_input("Bad", value=extracted_data[6], min_value=0)
                edit_miss = st.number_input("Miss", value=extracted_data[7], min_value=0)
            submitted = st.form_submit_button("확인 완료 및 저장하기")
            if submitted:
                cursor.execute('''
                    SELECT COUNT(*) FROM records 
                    WHERE play_date = ? AND song_title = ? 
                    AND perfect = ? AND great = ? AND good = ? AND bad = ? AND miss = ?
                ''', (edit_play_date, edit_song_title, edit_perfect, edit_great, edit_good, edit_bad, edit_miss))
                is_duplicate = cursor.fetchone()[0] > 0
                if is_duplicate:
                    st.write("안내: 이미 동일한 판정 수치와 날짜, 악곡 이름을 가진 중복 데이터가 존재하여 저장하지 않음.")
                else:
                    cursor.execute('''
                        INSERT INTO records (play_date, level, song_title, perfect, great, good, bad, miss, fast, late)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (edit_play_date, edit_level, edit_song_title, edit_perfect, edit_great, edit_good, edit_bad, edit_miss, edit_fast, edit_late))
                    conn.commit()
                    st.write("데이터베이스에 추출 결과를 성공적으로 저장함.")

with tab_view:
    st.write("저장된 결과 조회")
    df = pd.read_sql_query("SELECT * FROM records", conn)
    if not df.empty:
        song_list = df['song_title'].unique()
        selected_song = st.selectbox("조회할 악곡을 선택할 것", song_list)
        filtered_df = df[df['song_title'] == selected_song].copy()
        filtered_df = filtered_df.sort_values(by='play_date', ascending=True)
        display_df = filtered_df.drop(columns=['id'])
        st.dataframe(display_df, use_container_width=True)
    else:
        st.write("아직 저장된 기록이 없음.")