import streamlit as st
import requests
import pandas as pd

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
                    call_number = book.get("CallNumber", "")
                    cno = book.get("Cno", "")
                    isbn = ", ".join(book.get("ISBN", [])) if book.get("ISBN") else ""
                    
                    # 상세조회: 도서ID(Cno) 기반
                    if cno:
                        detail_url = f"https://ycc4.yc.ac.kr/cheetah/api/detail?Cno={cno}"
                        detail_res = requests.get(detail_url)
                        detail_json = detail_res.json()
                        rno_list = detail_json.get("RnoList", None)
                        
                        # 대출 가능한 도서만 표에 포함
                        if rno_list and isinstance(rno_list, list):
                            avail_count = 0
                            for copy in rno_list:
                                if copy.get("CFType") == "대출가능":
                                    avail_count += 1
                            # 만약 복본이 1권도 없으면 패스
                            if len(rno_list) == 0:
                                continue
                        else:
                            continue  # 실물 도서 아님 (예: 동영상 강의 등)
                    else:
                        continue  # Cno가 없으면 무시
                    
                    book_rows.append({
                        "제목": title,
                        "저자": author,
                        "청구기호": call_number,
                        "ISBN": isbn,
                        "도서ID": cno,
                        "대출가능권수": avail_count,
                    })
            
            df = pd.DataFrame(book_rows)
            st.dataframe(df)
            
        except Exception as e:
            st.error(f"오류 발생: {e}")
