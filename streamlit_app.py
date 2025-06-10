import streamlit as st
import requests

# ========== CONFIG ==========
BASE_URL = "https://ycc4.yc.ac.kr/"
DEFAULT_IMG = "https://via.placeholder.com/80x120.png?text=No+Image"
PAGE_SIZE = 10  # 한 번에 10개씩

def search_keyword_api(query, page, otwa1):
    url = BASE_URL + "cheetah/api/keyword"
    params = {
        "otwa1": otwa1,
        "otbool1": "A",
        "otpn1": "K",
        "otod1": query,
        "otwa2": "A",
        "otbool2": "A",
        "otpn2": "K",
        "otod2": "",
        "otwa3": "P",
        "otbool3": "A",
        "otpn3": "K",
        "otod3": "",
        "otopt": "all",
        "lang": "",
        "stype": "B",
        "sp": page,
        "otyear1": "",
        "otyear2": ""
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        return resp.json().get("items", [])
    except Exception as e:
        return []

def search_total_api(query, page, otwa1):
    url = BASE_URL + "cheetah/api/total"
    params = {
        "otod1": query,
        "otwa1": otwa1,
        "sp": page,
        "dc": PAGE_SIZE
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        return resp.json()
    except Exception:
        return []

def get_detail_api(cno):
    url = BASE_URL + "cheetah/api/detail"
    params = {"Cno": cno}
    try:
        resp = requests.get(url, params=params, timeout=5)
        return resp.json()
    except Exception:
        return {}

def parse_loan_available(rno_list):
    if not rno_list:
        return 0
    return sum(1 for item in rno_list if item.get("CFType") == "대출가능")

def parse_books_from_keyword(items, fav_cnos):
    results = []
    for item in items:
        cno = item.get("cno") or ""
        book = {
            "title": item.get("title", "제목 없음"),
            "author": item.get("author", "저자 없음"),
            "loanAvailable": int(item.get("kwon") or 0),
            "cno": cno,
            "coverImg": item.get("coverImg"),
            "isFavorite": cno in fav_cnos
        }
        results.append(book)
    return results

def parse_books_from_total(groups, fav_cnos, last_loaded_cnos):
    results = []
    for group in groups or []:
        items = group.get("item", [])
        for book in items:
            cno = book.get("Cno") or ""
            if not cno or cno in last_loaded_cnos:
                continue
            detail = get_detail_api(cno)
            avail_count = parse_loan_available(detail.get("RnoList"))
            cover_img = book.get("CoverImg") or detail.get("CoverImg")
            book_ui = {
                "title": book.get("Title", "정보 없음"),
                "author": book.get("Author", "정보 없음"),
                "loanAvailable": avail_count,
                "cno": cno,
                "coverImg": cover_img,
                "isFavorite": cno in fav_cnos
            }
            results.append(book_ui)
            last_loaded_cnos.add(cno)
    return results

def get_books(query, page, fav_cnos, last_loaded_cnos):
    # 1. IDX로 keyword → 결과 없으면 T로 retry
    for otwa1 in ["IDX", "T"]:
        keyword_items = search_keyword_api(query, page, otwa1)
        if keyword_items:
            return parse_books_from_keyword(keyword_items, fav_cnos)
        total_groups = search_total_api(query, page, otwa1)
        if total_groups:
            return parse_books_from_total(total_groups, fav_cnos, last_loaded_cnos)
    return []

# ================== STREAMLIT UI ====================

st.set_page_config("연암공과대학교 도서관 실시간 검색", layout="wide")

st.title("📚 연암공과대학교 도서관 실시간 대출 가능 검색")
query = st.text_input("도서명, 저자명 등 검색어를 입력하세요:", key="query_box")

if "fav_cnos" not in st.session_state:
    st.session_state.fav_cnos = set()
if "books" not in st.session_state:
    st.session_state.books = []
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "page" not in st.session_state:
    st.session_state.page = 1
if "last_loaded_cnos" not in st.session_state:
    st.session_state.last_loaded_cnos = set()
if "is_last_page" not in st.session_state:
    st.session_state.is_last_page = False

col_search, col_fav = st.columns(2)
with col_search:
    if st.button("검색", use_container_width=True, key="search_btn"):
        st.session_state.page = 1
        st.session_state.last_query = query
        st.session_state.last_loaded_cnos = set()
        st.session_state.books = get_books(query, 1, st.session_state.fav_cnos, st.session_state.last_loaded_cnos)
        st.session_state.is_last_page = not bool(st.session_state.books)
with col_fav:
    if st.button("즐겨찾기만 보기", use_container_width=True, key="fav_btn"):
        st.session_state.books = [
            book for book in st.session_state.books
            if book["cno"] in st.session_state.fav_cnos
        ]
        st.session_state.is_last_page = True

if st.session_state.books:
    for idx, book in enumerate(st.session_state.books):
        cols = st.columns([1, 4, 1])
        with cols[0]:
            st.image(book["coverImg"] or DEFAULT_IMG, width=60)
        with cols[1]:
            st.write(f'**{book["title"]}**')
            st.write(f'저자: {book["author"]}  |  대출 가능: {book["loanAvailable"]}권')
            st.write(f'청구기호: `{book["cno"]}`')
        with cols[2]:
            if book["isFavorite"]:
                if st.button("★", key=f"unfav_{idx}"):
                    st.session_state.fav_cnos.discard(book["cno"])
                    book["isFavorite"] = False
            else:
                if st.button("☆", key=f"fav_{idx}"):
                    st.session_state.fav_cnos.add(book["cno"])
                    book["isFavorite"] = True
    if not st.session_state.is_last_page:
        if st.button("더 보기", use_container_width=True, key="more_btn"):
            st.session_state.page += 1
            new_books = get_books(st.session_state.last_query, st.session_state.page, st.session_state.fav_cnos, st.session_state.last_loaded_cnos)
            if not new_books:
                st.session_state.is_last_page = True
            else:
                # cno 중복 방지
                existing_cnos = {b["cno"] for b in st.session_state.books}
                for book in new_books:
                    if book["cno"] not in existing_cnos:
                        st.session_state.books.append(book)
else:
    st.write("검색 결과가 없습니다.")
