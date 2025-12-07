import streamlit as st
from PIL import Image
import base64
from openai import OpenAI
import datetime

# 1. 페이지 설정
st.set_page_config(
    page_title="AI Photo Diary",
    layout="centered"
)

# --- 세션 상태 초기화 ---
if "api_key" not in st.session_state:
    st.session_state.api_key = None

if "diary_content" not in st.session_state:
    st.session_state.diary_content = ""

# --- 사이드바 로직 ---
with st.sidebar:
    if st.session_state.api_key:
        if "OPENAI_API_KEY" in st.secrets:
            st.success("✅ 서버의 API Key가 적용되었습니다.")
            st.info("개발자가 제공하는 키로 무료 이용 가능합니다.")
        else:
            st.success("✅ 사용자 API Key가 적용되었습니다!")
            if st.button("키 초기화 (로그아웃)"):
                st.session_state.api_key = None
                st.session_state.diary_content = "" 
                st.rerun()
    else:
        st.markdown("🔑 **OpenAI API Key 입력**")
        input_key = st.text_input("API Key", type="password")
        if st.button("적용하기"):
            st.session_state.api_key = input_key
            st.rerun()

    with st.expander("📖 사용 가이드", expanded=False):
        st.markdown("""
        **1단계**: API Key를 입력하고 적용하세요.
        
        **2단계**: 메인 화면에서 사진을 업로드하세요.
        
        **3단계**: '일기 쓰기' 버튼을 누르면 AI가 기록해줍니다.
        """)
    
    st.divider()
    st.caption("ⓒ 2025 AI Photo Diary")

# --- 메인 로직 시작 ---

if not st.session_state.api_key:
    st.title("AI Photo Diary 📸")
    st.write("---")
    st.info("👈 **왼쪽 사이드바**에서 OpenAI API Key를 입력하여 '로그인' 해주세요.")
    st.stop()

client = OpenAI(api_key=st.session_state.api_key)

st.title("AI Photo Diary 📝")
st.caption("사진을 업로드하고 메모를 남기면, AI가 당신의 하루를 감성적인 글로 기록해 드립니다.")
st.divider()

def encode_uploaded_file(file_obj):
    file_obj.seek(0)
    return base64.b64encode(file_obj.read()).decode("utf-8")

st.subheader("1. 사진 선택")
uploaded_files = st.file_uploader(
    "기록하고 싶은 사진들을 선택하세요", 
    type=['jpg', 'jpeg', 'png'], 
    accept_multiple_files=True
)

images_info = []

if uploaded_files:
    st.subheader("2. 상세 정보 입력")
    
    for uploaded_file in uploaded_files:
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                image = Image.open(uploaded_file)
                st.image(image, use_container_width=True)
                base64_image = encode_uploaded_file(uploaded_file)
            
            with col2:
                st.markdown(f"**🖼️ {uploaded_file.name}**")
                person_name = st.text_input("함께한 사람", key=f"person_{uploaded_file.name}", placeholder="예: 가족, 친구")
                location = st.text_input("장소", key=f"location_{uploaded_file.name}", placeholder="예: 한강 공원")
                keywords = st.text_input("활동/상황", key=f"keywords_{uploaded_file.name}", placeholder="예: 자전거 타기, 노을 구경")
            
            images_info.append({
                "file_name": uploaded_file.name,
                "base64_image": base64_image,
                "person": person_name if person_name else "",
                "location": location if location else "어딘가",
                "keywords": keywords if keywords else ""
            })
    
    st.divider()

    # --- [수정된 섹션] 3. 설정 및 생성 (모델 선택 포함) ---
    st.subheader("3. 설정 및 생성")
    
    # 분위기와 모델 선택을 2개의 컬럼으로 나란히 배치
    col_opt1, col_opt2 = st.columns(2)
    
    with col_opt1:
        mood = st.text_input("오늘의 분위기 (선택사항)", placeholder="예: 차분한, 활기찬")
        
    with col_opt2:
        # 모델 선택 셀렉트박스
        model_option = st.selectbox(
            "AI 모델 선택", 
            ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "직접 입력"],
            help="gpt-4o-mini: 빠름(추천) / gpt-4o: 고성능"
        )
        # 직접 입력을 선택했을 때만 나타나는 텍스트창
        if model_option == "직접 입력":
            custom_model = st.text_input("모델명 입력", placeholder="예: gpt-5", label_visibility="collapsed")
            selected_model = custom_model if custom_model else "gpt-4o-mini"
        else:
            selected_model = model_option

    # 버튼을 하단에 꽉 차게 배치
    st.write("")
    generate_btn = st.button("일기 쓰기 ✨", type="primary", use_container_width=True)

    if generate_btn:
        with st.spinner(f"[{selected_model}] 모델이 글을 쓰고 있습니다..."):
            diary_prompt = """오늘 찍은 사진들을 보고 일기를 작성해주세요.
            각 사진과 함께 장소, 함께한 사람들, 활동 키워드가 제공됩니다.
            이 정보들을 자연스럽게 활용하여 실제 있었던 일만을 서술해주세요.
            """
            diary_prompt += "**입력된 사진 정보** (순서대로 작성해주세요):\n"

            for info in images_info:
                diary_prompt += (
                    f"- 사진 파일: {info['file_name']}\n"
                    f"  장소: {info['location']}\n"
                    f"  함께한 사람: {info['person']}\n"
                    f"  키워드: {info['keywords']}\n\n"
                )
            
            base_guidelines = """
            **일기 작성 가이드라인**:
            1. **일기의 주체는 "나"**이며, 1인칭 시점으로 작성하세요.
            2. 사진의 시각적 요소와 입력된 텍스트 정보를 결합하여 자연스럽게 서술하세요.
            3. 날짜나 요일은 본문에 포함하지 마세요 (별도 표시됨).
            4. 억지로 꾸미려 하지 말고, 담백하고 솔직한 문체로 작성하세요.
            """

            if mood.strip():
                diary_prompt += base_guidelines + f'\n5. **작성 분위기**: "{mood}"'
            else:
                diary_prompt += base_guidelines

            message_content = [{"type": "text", "text": diary_prompt}]
            for info in images_info:
                message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{info['base64_image']}"}
                })

            try:
                # [핵심] 선택된 모델 변수(selected_model) 사용
                response = client.chat.completions.create(
                    model=selected_model, 
                    messages=[
                        {"role": "system", "content": "당신은 세련된 에세이 작가입니다."},
                        {"role": "user", "content": message_content}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                st.session_state.diary_content = response.choices[0].message.content
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")

    # 결과 표시 및 편집 영역
    if st.session_state.diary_content:
        today = datetime.date.today()
        weekday_str = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        formatted_date = f"{today.year}년 {today.month}월 {today.day}일 {weekday_str[today.weekday()]}"

        st.divider()
        st.subheader(f"📅 {formatted_date}")
        st.caption(f"작성된 모델: {selected_model}") # 어떤 모델로 썼는지 표시
        
        st.info("아래 내용을 자유롭게 수정할 수 있습니다.")
        edited_diary = st.text_area(
            "일기 내용 편집",
            value=st.session_state.diary_content,
            height=400,
            label_visibility="collapsed"
        )

else:
    with st.container(border=True):
        st.write("📂 위의 **'Browse files'** 버튼을 눌러 사진을 추가해주세요.")
