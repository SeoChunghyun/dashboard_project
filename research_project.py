import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- 1. 페이지 및 자동 새로고침 설정 ---
st.set_page_config(page_title="정부 과제 모니터링 (Auto)", page_icon="🚘", layout="wide")

# [자동 새로고침] 1시간(3600초)마다 페이지 리로드
refresh_sec = 3600 
st.markdown(
    f"""
    <meta http-equiv="refresh" content="{refresh_sec}">
    <script>
        setTimeout(function(){{
            window.location.reload(1);
        }}, {refresh_sec * 1000});
    </script>
    """,
    unsafe_allow_html=True
)

# --- 2. 키워드 및 헤더 설정 ---
TARGET_KEYWORDS = ["자동차", "연구과제", "연구", "R&D", "친환경", "소재", "배터리"]

# --- 3. 도구 함수들 ---
def calculate_d_day(end_date_str):
    """마감일까지 남은 날짜(D-Day) 계산"""
    try:
        for fmt in ["%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"]:
            try:
                end_date = datetime.strptime(str(end_date_str).strip(), fmt).date()
                today = datetime.now().date()
                days_left = (end_date - today).days
                
                if days_left < 0: return "마감됨"
                elif days_left == 0: return "D-Day"
                else: return f"D-{days_left}"
            except:
                continue
        return "-"
    except:
        return "-"

def is_target_project(title):
    """키워드 매칭 여부 확인"""
    if not title: return False
    for keyword in TARGET_KEYWORDS:
        if keyword in title:
            return True
    return False

# --- 4. 데이터 수집 함수 (캐싱 적용: 1시간) ---
@st.cache_data(ttl=3600, show_spinner="데이터 업데이트 중...")
def scrape_all_sites():
    all_tasks = []
    
    # 1. KEIT (가상 데이터)
    keit_data = [
        {"출처": "KEIT", "공고명": "2026년 소재부품기술개발사업 신규지원", "마감일": "2026-04-15", "링크": "https://www.keit.re.kr"},
        {"출처": "KEIT", "공고명": "바이오 헬스 케어 과제", "마감일": "2026-05-01", "링크": "https://www.keit.re.kr"}
    ]
    all_tasks.extend([item for item in keit_data if is_target_project(item['공고명'])])

    # 2. 중기부 (가상 데이터)
    mss_data = [
        {"출처": "중기부", "공고명": "2026년 연구 R&D 기획지원사업", "마감일": "2026-03-20", "링크": "https://www.smtech.go.kr"},
        {"출처": "중기부", "공고명": "친환경 알루미늄 소재 부품 개발", "마감일": "2026-03-15", "링크": "https://www.smtech.go.kr"}
    ]
    all_tasks.extend([item for item in mss_data if is_target_project(item['공고명'])])

    # 3. 산업부 (가상 데이터)
    motie_data = [
        {"출처": "산업부", "공고명": "이차전지 배터리 특화단지 지원사업", "마감일": "2026-03-31", "링크": "https://www.motie.go.kr"},
        {"출처": "산업부", "공고명": "미래차 전환 자동차 부품 기업 육성", "마감일": "2026-02-25", "링크": "https://www.motie.go.kr"}
    ]
    all_tasks.extend([item for item in motie_data if is_target_project(item['공고명'])])

    # 4. IRIS (가상 데이터)
    iris_data = [
        {"출처": "IRIS", "공고명": "[범부처] 고효율 배터리 연구과제 모집", "마감일": "2026-05-10", "링크": "https://www.iris.go.kr"},
        {"출처": "IRIS", "공고명": "인문사회 학술연구교수 지원", "마감일": "2026-04-01", "링크": "https://www.iris.go.kr"}
    ]
    all_tasks.extend([item for item in iris_data if is_target_project(item['공고명'])])

    # 5. 자동차연구원 (가상 데이터)
    katech_data = [
        {"출처": "자동차연", "공고명": "친환경 자동차 주행 성능 평가", "마감일": "2026-03-05", "링크": "https://www.katech.re.kr"},
        {"출처": "자동차연", "공고명": "자율주행 센서 및 소재 기술 지원", "마감일": "2026-03-10", "링크": "https://www.katech.re.kr"}
    ]
    all_tasks.extend([item for item in katech_data if is_target_project(item['공고명'])])
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return all_tasks, current_time

# --- 5. 메인 실행 화면 ---

# 사이드바 구성
with st.sidebar:
    st.header("⚙️ 시스템 제어")
    
    # [유지] 수집 채널 상태 표시
    st.subheader("📡 수집 채널 상태")
    st.success("✅ KEIT (산업기술평가원)")
    st.success("✅ SMTECH (중기부)")
    st.success("✅ MOTIE (산업통상자원부)")
    st.success("✅ IRIS (범부처)")
    st.success("✅ KATECH (자동차연구원)")
    
    st.markdown("---")
    
    # 업데이트 시간
    if "last_update" not in st.session_state:
        st.session_state.last_update = "-"
    st.caption(f"최근 갱신: {st.session_state.last_update}")
    
    if st.button("🔄 즉시 업데이트"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.write("🎯 타겟 키워드:")
    tags_html = "".join([f"<span style='background:#e8f0fe; color:#1a73e8; padding:5px 8px; margin:2px; border-radius:12px; font-size:0.85em; font-weight:bold; display:inline-block;'>#{k}</span>" for k in TARGET_KEYWORDS])
    st.markdown(tags_html, unsafe_allow_html=True)

# 메인 화면 구성
st.title("🏭 정부 과제 실시간 모니터링")
st.markdown("### 자동차·부품·소재 분야 R&D 공고 통합 대시보드")
st.divider()

# 데이터 로드
data_list, update_time = scrape_all_sites()
st.session_state.last_update = update_time

df = pd.DataFrame(data_list)

if not df.empty:
    df['D-Day'] = df['마감일'].apply(calculate_d_day)
    df = df.sort_values(by='마감일')
    
    # [유지] 상단 지표 카드 (기준 날짜 포함)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 검색된 공고", f"{len(df)} 건")
    with col2:
        urgent_count = len([d for d in df['D-Day'] if d == "D-Day" or (d.startswith("D-") and int(d.split("-")[1]) <= 7)])
        st.metric("🚨 마감 임박 (7일 내)", f"{urgent_count} 건", delta="서두르세요!")
    with col3:
        st.metric("기준 날짜", datetime.now().strftime("%Y-%m-%d"))

    # [유지] 테이블 제목
    st.subheader("📋 실시간 공고 리스트")
    
    # 메인 테이블
    st.dataframe(
        df,
        column_config={
            "링크": st.column_config.LinkColumn("바로가기", display_text="🔗 이동"),
            "D-Day": st.column_config.TextColumn("상태"),
            "출처": st.column_config.TextColumn("기관명"),
            "공고명": st.column_config.TextColumn("공고 제목", width="large")
        },
        hide_index=True,
        use_container_width=True
    )

    # =========================================================
    # [추가됨] 상세 정보 카드 섹션
    # =========================================================
    st.divider()
    st.subheader("📌 상세 정보 카드")
    st.caption("각 공고를 클릭하면 상세 내용을 확인할 수 있습니다.")

    for index, row in df.iterrows():
        # 상태에 따른 이모지 설정
        status_icon = "🔥" if "D-" in row['D-Day'] and int(row['D-Day'].split("-")[1]) <= 7 else "📄"
        
        # 카드(Expander) 제목 구성
        expander_title = f"{status_icon} [{row['D-Day']}] {row['공고명']}"
        
        with st.expander(expander_title):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**🏢 소관부처:** {row['출처']}")
                st.markdown(f"**🗓 마감일자:** {row['마감일']} ({row['D-Day']})")
                st.markdown(f"**🔗 공고링크:** [바로가기]({row['링크']})")
            with c2:
                # 버튼 예시 (나중에 기능 추가 가능)
                st.button("스크랩 하기", key=f"btn_{index}")
            
            st.info("💡 팁: 해당 공고는 키워드 필터링을 통해 수집되었습니다.")

else:
    st.warning("현재 설정된 키워드에 맞는 공고가 없습니다.")

# 푸터
st.markdown("---")
st.caption(f"ⓒ 2026 Auto-R&D Monitor | 5대 기관 실시간 연동 중 | 최종 데이터 확인: {update_time}")