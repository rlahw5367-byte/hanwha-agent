import streamlit as st
from streamlit_echarts import st_echarts

st.title("Echart - 검색 정확도 게이지 출력")

options = {
    "series": [{
        "type": "gauge", 
        "min": 0, 
        "max": 100, 
        "detail": {"formatter": "{vale}%"}, 
        "data": [{"value": 84, "name": "정확도"}]
    }]
}

st_echarts(options=options, height="320px")
