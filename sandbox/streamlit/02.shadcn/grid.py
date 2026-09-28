import streamlit as st
import pandas as pd 
from st_aggrid import AgGrid, GridOptionsBuilder

st.title("AgGrid - 정렬과 필터가 붙은 테이블")

df = pd.DataFrame([
    {"문서ID": "DOC-HR-014", "문서명": "국내출장 여비 규정", "상태": "현행", "청크": 70},
    {"문서ID": "DOC-SE-011", "문서명": "장비 반출입 절차", "상태": "만료", "청크": 24},
    {"문서ID": "DOC-PU-007", "문서명": "구매·계약 규정", "상태": "현행", "청크": 58},
])


gb = GridOptionsBuilder.from_dataframe(df)

gb.configure_default_column(sortable=True, filter=True)
gb.configure_selection("single")

AgGrid(df, gridOtions=gb.build(), height=240)
