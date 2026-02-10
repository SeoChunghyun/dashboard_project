import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3
import time

# [설정] SSL 보안 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="정부 과제 모니터링 (Custom)", page_icon="⚙️", layout="wide")

# [자동 새로고침] 1시간
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

# --- 2. [핵심] 키워드 관리 시스템 (Session State) ---
# 프로그램이 처음 실행될 때 기본 키워드를 설정합니다.
if 'my_keywords' not in st.session_state:
    st.session_state.my_keywords = ["자동차", "연구과제", "연구", "R&D", "친환경", "소재", "배터리", "모빌리티"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive"
}

# --- 3. 도구 함수들 ---
def calculate_d_day(date_str):
    if not date_str or date_str == "-": return "-"
    try:
        clean = str(date_str).replace(".", "-").replace("/", "-").strip()
        end_date = datetime.strptime(clean, "%Y-%m-%d").date()
        today = datetime.now().date()
        diff = (end_date - today).days
        
        if diff < 0: return "마감됨"
        elif diff == 0: return "D-Day"
        else: return f"D-{diff}"
    except:
        return "-"

def is_target(title, keywords_list):
    """제목에 사용자가 설정한 키워드가 있는지 확인"""
    if not title: return False
    for k in keywords_list:
        if k in title: return True
    return False

def get_soup(url):
    try:
        res = requests.get(url, headers=HEADERS, verify=False, timeout=10)
        res.encoding = res.apparent_encoding
        if res.status_code == 200:
            return BeautifulSoup(res.text, "html.parser")
    except: pass
    return None

# --- 4. 크롤링 함수들 (키워드 리스트를 인자로 받음) ---
def scrape_keit(keywords):
    results = []
    url = "https://www.keit.re.kr/board/list.do?boardId=BBS_0000004"
    try:
        soup = get_soup(url)
        if soup:
            rows = soup.select("table tbody tr")
            for row in rows:
                try:
                    title_tag = row.select_one("td.subject a") or row.select_one("a")
                    date_tag = row.select_one("td:nth-child(5)")
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        date_txt = date_tag.get_text(strip=True) if date_tag else "-"
                        if is_target(title, keywords):
                            results.append({"출처": "KEIT", "공고명": title, "마감일": date_txt, "링크": url})
                except: continue
    except: pass
    return results

def scrape_mss(keywords):
    results = []
    url = "https://www.smtech.go.kr/front/ifg/no/notice01_list.do"
    try:
        soup = get_soup(url)
        if soup:
            rows = soup.select("table.tbl_list tbody tr")
            for row in rows:
                try:
                    title_tag = row.select_one("td.l a")
                    date_tag = row.select_one("td:nth-child(4)")
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        date_txt = date_tag.get_text(strip=True) if date_tag else "-"
                        if is_target(title, keywords):
                            results.append({"출처": "SMTECH", "공고명": title, "마감일": date_txt, "링크": url})
                except: continue
    except: pass
    return results

def scrape_motie(keywords):
    results = []
    url = "https://www.motie.go.kr/kor/article/ATCL3f49a5a8c/list.do"
    try:
        soup = get_soup(url)
        if soup:
            rows = soup.select("table tbody tr")
            for row in rows:
                try:
                    title_tag = row.select_one("td.subject a")
                    date_tag = row.select_one("td.date")
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        date_txt = date_tag.get_text(strip=True) if date_tag else datetime.now().strftime("%Y-%m-%d")
                        if is_target(title, keywords):
                            results.append({"출처": "MOTIE", "공고명": title, "마감일": date_txt, "링크": url})
                except: continue
    except: pass
    return results

def scrape_iris(keywords):
    results = []
    url = "https://www.iris.go.kr/contents/retrieveBusAnnouncementList.do"
    try:
        soup = get_soup(url)
        if soup:
            rows = soup.select("table tbody tr")
            for row in rows:
                try:
                    title_tag = row.select_one("td.tit a") or row.select_one("a")
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        if is_target(title, keywords):
                            results.append({"출처": "IRIS", "공고명": title, "마감일": "-", "링크": url})
                except: continue
    except: pass
    return results

def scrape_katech(keywords):
    results = []
    url = "https://www.katech.re.kr/katech/notice/notice.do"
    try:
        soup = get_soup(url)
        if soup:
            rows = soup.select("tbody tr")
            for row in rows:
                try:
                    title_tag = row.select_one("td.subject a")
                    date_tag = row.select_one("td.date")
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        date_txt = date_tag.get_text(strip=True) if date_tag else "-"
                        if is_target(title, keywords):
                            results.append({"출처": "KATECH", "공고명": title, "마감일": date_txt, "링크": url})
                except: continue
    except: pass
    return results

# --- 5. 데이터 통합 함수 (키워드가 바뀌면 캐시를 갱신해야 함) ---
@st.cache_data(ttl=3600, show_spinner="📡 설정된 키워드로 스캔 중...")
def scrape_all_real_data(current_keywords):
    """
    current_keywords 인자를 받아서, 키워드가 바뀔 때마다 
    새로 크롤링을 하도록 만듭니다.
    """
    all_tasks = []
    
    all_tasks.extend(scrape_keit(current_keywords))
    all_tasks.extend(scrape_mss(current_keywords))
    all_tasks.extend(scrape_motie(current_keywords))
    all_tasks.extend(scrape_iris(current_keywords))
    all_tasks.extend(scrape_katech(current_keywords))
    
    return all_tasks, datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- 6. 메인 화면 ---

with st.sidebar:
    st.header("⚙️ 관제 센터 설정")
    
    # [새로운 기능] 키워드 추가/삭제 UI
    st.subheader("🎯 타겟 키워드 관리")
    
    # 1. 키워드 추가 입력창
    new_keyword = st.text_input("추가할 키워드 입력", placeholder="예: 반도체")
    if st.button("키워드 추가"):
        if new_keyword and new_keyword not in st.session_state.my_keywords:
            st.session_state.my_keywords.append(new_keyword)
            st.rerun() # 화면 즉시 새로고침
        elif new_keyword in st.session_state.my_keywords:
            st.warning("이미 존재하는 키워드입니다.")

    # 2. 키워드 확인 및 삭제 (멀티셀렉트 박스 이용)
    # 사용자가 여기서 X를 눌러 삭제하면 session_state에 즉시 반영
    selected_keywords = st.multiselect(
        "현재 적용된 키워드 (삭제하려면 X 클릭)",
        options=st.session_state.my_keywords,
        default=st.session_state.my_keywords
    )
    
    # 만약 멀티셀렉트에서 내용이 바뀌었다면(삭제 등), 세션 상태 업데이트
    if set(selected_keywords) != set(st.session_state.my_keywords):
        st.session_state.my_keywords = selected_keywords
        st.rerun()

    st.markdown("---")
    
    st.subheader("📡 수집 채널 상태")
    st.success("✅ 시스템 가동 중")
    
    if st.button("🔄 즉시 업데이트"):
        st.cache_data.clear()
        st.rerun()

st.title("🏭 정부 과제 실시간 모니터링 (Custom)")
st.markdown("### 📡 내가 설정한 키워드로 5대 기관을 실시간 스캔합니다.")
st.divider()

# 현재 설정된 키워드로 크롤링 실행
current_keywords_list = st.session_state.my_keywords
data_list, update_time = scrape_all_real_data(current_keywords_list)
df = pd.DataFrame(data_list)

if not df.empty:
    df['D-Day'] = df['마감일'].apply(calculate_d_day)
    
    # 상단 지표
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("수집된 공고", f"{len(df)} 건")
    with col2:
        urgent_count = 0
        for d in df['D-Day']:
            if d == "D-Day": urgent_count += 1
            elif str(d).startswith("D-"):
                try:
                    if int(d.split("-")[1]) <= 7: urgent_count += 1
                except: pass
        st.metric("🚨 마감 임박", f"{urgent_count} 건")
    with col3:
        st.metric("기준 날짜", datetime.now().strftime("%Y-%m-%d"))

    st.subheader("📋 실시간 공고 리스트")
    st.dataframe(
        df,
        column_config={
            "링크": st.column_config.LinkColumn("바로가기", display_text="🔗 이동"),
            "D-Day": st.column_config.TextColumn("상태"),
            "공고명": st.column_config.TextColumn("공고 제목", width="large")
        },
        hide_index=True,
        use_container_width=True
    )

    st.divider()
    st.subheader("📌 상세 정보 카드")
    for index, row in df.iterrows():
        icon = "📄"
        d_val = str(row['D-Day'])
        if d_val == "D-Day": icon = "🔥"
        elif d_val.startswith("D-"):
            try:
                if int(d_val.split("-")[1]) <= 7: icon = "🔥"
            except: pass
            
        with st.expander(f"{icon} [{d_val}] {row['공고명']}"):
            st.write(f"**기관:** {row['출처']}")
            st.write(f"**마감:** {row['마감일']}")
            st.markdown(f"**[게시판 바로가기]({row['링크']})**")

else:
    st.warning("📢 현재 설정된 키워드로 검색된 공고가 없습니다.")
    st.info(f"🔍 현재 키워드: {', '.join(current_keywords_list)}")
    st.write("사이드바에서 키워드를 추가하거나 변경해 보세요.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("수집된 공고", "0 건")
    col2.metric("마감 임박", "0 건")
    col3.metric("기준 날짜", datetime.now().strftime("%Y-%m-%d"))

st.markdown("---")
st.caption(f"최종 업데이트: {update_time}")
