import streamlit as st
import requests
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# 커스텀 CSS: 표 배경을 연한 하늘색으로 변경
st.markdown("""
    <style>
    .ag-root-wrapper, .ag-theme-alpine {
        background-color: #e6f2ff !important;   /* 연한 하늘색 */
    }
    .ag-row {
        background-color: #f4faff !important;   /* 더 연하게 */
    }
    .ag-header {
        background-color: #cce7ff !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("연암공과대학교 도서관 도서 실시간 대출 가능 여부 검색기")

query = st.text_input("도서명, 저자명 등 검색어를 입력하세요:")

if st.button("검색"):
    with st.spinner("도서 목록을 불러오고 있습니다..."):
        try:
            url = f"https://ycc4.yc.ac.kr/cheetah/api/total?otod1={query}&otwa1=IDX&sp=1&dc=30"
            res = requests.get(url)
            data = res.json()
            book_rows = []

            for group in data:
                items = group.get("item", [])
                for book in items:
                    title = book.get("Title", "")
                    author = book.get("Author", "")
                    cno = book.get("Cno", "")

                    if cno:
                        detail_url = f"https://ycc4.yc.ac.kr/cheetah/api/detail?Cno={cno}"
                        detail_res = requests.get(detail_url)
                        detail_json = detail_res.json()
                        rno_list = detail_json.get("RnoList", None)

                        if rno_list and isinstance(rno_list, list):
                            avail_count = sum(1 for copy in rno_list if copy.get("CFType") == "대출가능")
                            if len(rno_list) == 0:
                                continue
                        else:
                            continue
                    else:
                        continue

                    book_rows.append({
                        "제목": title,
                        "저자": author,
                        "대출가능권수": avail_count,
                    })

            df = pd.DataFrame(book_rows, columns=["제목", "저자", "대출가능권수"])

            # 컬럼 별 넓이 넉넉히
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_column("제목", wrapText=True, autoHeight=True, width=500)
            gb.configure_column("저자", width=350)
            gb.configure_column("대출가능권수", width=150)
            gridOptions = gb.build()
            AgGrid(
                df,
                gridOptions=gridOptions,
                fit_columns_on_grid_load=False,
                theme="alpine",
                height=600,
                width=1200,  # 가로 넓게
                enable_enterprise_modules=False,
            )
        except Exception as e:
            st.error(f"오류 발생: {e}")
