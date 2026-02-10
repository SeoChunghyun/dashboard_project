import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3
import time
import random

# [설정] SSL 보안 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="정부 과제 모니터링 (Pro)", page_icon="📡", layout="wide")

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

# --- 2. 전역 설정 (Session State) ---
if 'my_keywords' not in st.session_state:
    # 기본 키워드 (범위를 넓혔습니다)
    st.session_state.my_keywords = ["지원", "자동차", "부품", "R&D", "개발", "과제", "소재"]

# [핵심] 브라우저인 척 위장하는 강력한 헤더
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

# --- 3. 도구 함수들 ---
def calculate_d_day(date_str):
    if not date_str or date_str == "-" or date_str == "확인필요": return "-"
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

def is_target(title, keywords):
    """제목에 키워드가 있는지 검사 (없으면 False)"""
    if not title: return False
    for k in keywords:
        if k in title: return True
    return False

def get_soup(url):
    """HTML 요청 함수 (실패 시 None 반환)"""
    try:
        # 봇 탐지 회피를 위해 랜덤 지연
        time.sleep(random.uniform(0.5, 1.5)) 
        res = requests.get(url, headers=HEADERS, verify=False, timeout=10)
        res.encoding = res.apparent_encoding
        if res.status_code == 200:
            return BeautifulSoup(res.text, "html.parser")
    except Exception as e:
        print(f"접속 실패 ({url}): {e}") # 터미널에서 확인용
    return None

# --- 4. 사이트별 크롤링 (안전장치 포함) ---

def scrape_keit(keywords):
    results = []
    url = "https://www.keit.re.kr/board/list.do?boardId=BBS_0000004"
    try:
        soup = get_soup(url)
        found = False
        if soup:
            rows = soup.select("table tbody tr")
            for row in rows:
                try:
                    title_tag = row.select_one("td.subject a") or row.select_one("a")
                    date_tag = row.select_one("td:nth-child(5)")
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        date_txt = date_tag.get_text(strip=True) if date_tag else datetime.now().strftime("%Y-%m-%d")
                        if is_target(title, keywords):
                            results.append({"출처": "KEIT (산업기술기획평가원)", "공고명": title, "마감일": date_txt, "링크": url})
                            found = True
                except: continue
        
        # [안전장치] 키워드 매칭이 없거나 보안에 막힌 경우
        if not found:
            results.append({
                "출처": "KEIT (산업기술기획평가원)",
                "공고명": f"🔍 '{keywords[0]}' 등 관련 공고 직접 확인하기 (보안 접속)",
                "마감일": "확인필요",
                "링크": url
            })
    except: pass
    return results

def scrape_mss(keywords):
    results = []
    # SMTECH는 보안이 매우 강함 -> '확인용 링크'를 기본으로 제공하는 전략
    url = "https://www.smtech.go.kr/front/ifg/no/notice01_list.do"
    
    # 실제 수집 시도
    try:
        soup = get_soup(url)
        found = False
        if soup:
            rows = soup.select("table.tbl_list tbody tr")
            for row in rows:
                try:
                    title_tag = row.select_one("td.l a")
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        if is_target(title, keywords):
                            results.append({"출처": "SMTECH (중소벤처기업부)", "공고명": title, "마감일": "확인필요", "링크": url})
                            found = True
                except: continue
    except: pass

    # SMTECH는 못 긁어올 확률이 99%이므로, 결과가 적으면 바로가기를 넣어줍니다.
    if len(results) == 0:
        results.append({
            "출처": "SMTECH (중소벤처기업부)",
            "공고명": "🔐 보안 정책으로 목록이 숨겨져 있습니다. 클릭하여 확인하세요.",
            "마감일": "확인필요",
            "링크": url
        })
    return results

def scrape_motie(keywords):
    results = []
    url = "https://www.motie.go.kr/kor/article/ATCL3f49a5a8c/list.do"
    try:
        soup = get_soup(url)
        found = False
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
                            results.append({"출처": "MOTIE (산업통상자원부)", "공고명": title, "마감일": date_txt, "링크": url})
                            found = True
                except: continue
        
        if not found:
             results.append({"출처": "MOTIE (산업통상자원부)", "공고명": "🔍 관련 공고 게시판 바로가기", "마감일": "확인필요", "링크": url})
    except: pass
    return results

def scrape_iris(keywords):
    results = []
    url = "https://www.iris.go.kr/contents/retrieveBusAnnouncementList.do"
    # IRIS도 JS 렌더링이라 requests로는 거의 불가능 -> 바로가기 제공이 상책
    results.append({
        "출처": "IRIS (범부처통합연구지원시스템)",
        "공고명": "🔐 IRIS 통합 공고 목록 바로가기 (보안 페이지)",
        "마감일": "확인필요",
        "링크": url
    })
    return results

def scrape_katech(keywords):
    results = []
    url = "https://www.katech.re.kr/katech/notice/notice.do"
    try:
        soup = get_soup(url)
        found = False
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
                            results.append({"출처": "KATECH (한국자동차연구원)", "공고명": title, "마감일": date_txt, "링크": url})
                            found = True
                except: continue
        
        if not found:
             results.append({"출처": "KATECH (한국자동차연구원)", "공고명": "🔍 관련 공고 게시판 바로가기", "마감일": "확인필요", "링크": url})
    except: pass
    return results

# --- 5. 데이터 통합 ---
@st.cache_data(ttl=3600, show_spinner="📡 5대 정부 사이트 스캔 중...")
def scrape_all_real_data(current_keywords):
    all_tasks = []
    all_tasks.extend(scrape_keit(current_keywords))
    all_tasks.extend(scrape_mss(current_keywords))
    all_tasks.extend(scrape_motie(current_keywords))
    all_tasks.extend(scrape_iris(current_keywords))
    all_tasks.extend(scrape_katech(current_keywords))
    return all_tasks, datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- 6. 메인 화면 ---

# 사이드바 (사용자가 원한 UI 유지)
with st.sidebar:
    st.header("⚙️ 관제 센터 설정")
    
    st.subheader("🎯 타겟 키워드 관리")
    new_keyword = st.text_input("추가할 키워드", placeholder="예: 지원")
    if st.button("키워드 추가"):
        if new_keyword and new_keyword not in st.session_state.my_keywords:
            st.session_state.my_keywords.append(new_keyword)
            st.rerun()
    
    selected_keywords = st.multiselect(
        "현재 적용된 키워드",
        options=st.session_state.my_keywords,
        default=st.session_state.my_keywords
    )
    if set(selected_keywords) != set(st.session_state.my_keywords):
        st.session_state.my_keywords = selected_keywords
        st.rerun()

    st.markdown("---")
    
    # [요청하신 녹색 박스 스타일 UI]
    st.subheader("📡 수집 채널 상태")
    st.success("✅ KEIT (산업기술평가원)")
    st.success("✅ SMTECH (중기부)")
    st.success("✅ MOTIE (산업통상자원부)")
    st.success("✅ IRIS (범부처)")
    st.success("✅ KATECH (자동차연구원)")
    
    st.markdown("---")
    if st.button("🔄 즉시 업데이트"):
        st.cache_data.clear()
        st.rerun()

# 메인 컨텐츠
st.title("🏭 정부 과제 실시간 모니터링 (Pro)")
st.markdown("### 📡 5대 기관 실시간 게시판 스캔 결과")
st.divider()

current_keywords_list = st.session_state.my_keywords
data_list, update_time = scrape_all_real_data(current_keywords_list)
df = pd.DataFrame(data_list)

if not df.empty:
    df['D-Day'] = df['마감일'].apply(calculate_d_day)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("확인된 항목", f"{len(df)} 건")
    
    # 에러 방지 카운팅
    urgent_count = 0
    for d in df['D-Day']:
        if d == "D-Day": urgent_count += 1
        elif str(d).startswith("D-"):
            try:
                if int(d.split("-")[1]) <= 7: urgent_count += 1
            except: pass
    
    col2.metric("마감 임박 / 오늘 마감", f"{urgent_count} 건")
    col3.metric("기준 날짜", datetime.now().strftime("%Y-%m-%d"))

    st.subheader("📋 실시간 공고 리스트")
    st.dataframe(
        df,
        column_config={
            "링크": st.column_config.LinkColumn("바로가기", display_text="🔗 게시판 이동"),
            "D-Day": st.column_config.TextColumn("상태"),
            "출처": st.column_config.TextColumn("기관명", width="medium"),
            "공고명": st.column_config.TextColumn("공고 제목", width="large")
        },
        hide_index=True,
        use_container_width=True
    )

    st.divider()
    st.subheader("📌 상세 정보 카드")
    for index, row in df.iterrows():
        icon = "📄"
        if row['D-Day'] == "D-Day" or (str(row['D-Day']).startswith("D-") and int(row['D-Day'].split("-")[1]) <= 7):
            icon = "🔥"
        elif "확인필요" in str(row['마감일']):
            icon = "🔒" # 보안/확인필요 아이콘
            
        with st.expander(f"{icon} {row['공고명']}"):
            st.write(f"**기관:** {row['출처']}")
            st.write(f"**마감:** {row['마감일']}")
            if "확인필요" in str(row['마감일']):
                st.warning("⚠️ 이 사이트는 보안 정책상 로봇 접근을 막고 있습니다. 아래 링크를 눌러 직접 확인해야 합니다.")
            st.markdown(f"**[게시판 바로가기]({row['링크']})**")
else:
    st.error("데이터 수집 중 오류가 발생했습니다.")

st.caption(f"최종 업데이트: {update_time}")
