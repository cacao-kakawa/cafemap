import pandas as pd
import folium
from folium.plugins import MarkerCluster
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="제주 스터디카페 지도", page_icon="📚", layout="wide")

CSV_PATH = "제주상권.csv"
TARGET_CATEGORY = "독서실/스터디 카페"


@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH, encoding="cp949")
    df = df[df["상권업종소분류명"] == TARGET_CATEGORY].copy()
    df = df.dropna(subset=["경도", "위도"])
    keep_cols = ["상호명", "시군구명", "행정동명", "도로명주소", "지번주소", "경도", "위도"]
    df = df[keep_cols].reset_index(drop=True)
    return df


df = load_data()

st.title("📚 제주도 스터디카페 지도")
st.caption(f"소상공인시장진흥공단 제주상권정보 기준 · '{TARGET_CATEGORY}' 업종 · 총 {len(df)}곳")

with st.sidebar:
    st.header("필터")
    regions = ["전체"] + sorted(df["시군구명"].unique().tolist())
    selected_region = st.selectbox("시군구", regions)

    keyword = st.text_input("상호명 검색", "")

filtered = df.copy()
if selected_region != "전체":
    filtered = filtered[filtered["시군구명"] == selected_region]
if keyword:
    filtered = filtered[filtered["상호명"].str.contains(keyword, case=False, na=False)]

st.subheader(f"검색 결과: {len(filtered)}곳")

col_map, col_list = st.columns([2, 1])

with col_map:
    if len(filtered) > 0:
        center_lat = filtered["위도"].mean()
        center_lon = filtered["경도"].mean()
    else:
        center_lat, center_lon = 33.38, 126.55

    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap")
    cluster = MarkerCluster().add_to(m)

    for _, row in filtered.iterrows():
        address = row["도로명주소"] if pd.notna(row["도로명주소"]) else row["지번주소"]
        popup_html = f"<b>{row['상호명']}</b><br>{address}"
        folium.Marker(
            location=[row["위도"], row["경도"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=row["상호명"],
            icon=folium.Icon(color="blue", icon="book", prefix="fa"),
        ).add_to(cluster)

    st_folium(m, width=None, height=600, returned_objects=[])

with col_list:
    st.dataframe(
        filtered[["상호명", "시군구명", "행정동명", "도로명주소"]],
        width="stretch",
        height=600,
        hide_index=True,
    )

st.divider()
st.header("📊 분석")

if len(filtered) == 0:
    st.info("표시할 데이터가 없습니다.")
else:
    region_counts = filtered["시군구명"].value_counts()
    dong_counts = filtered["행정동명"].value_counts()

    m1, m2, m3 = st.columns(3)
    m1.metric("총 스터디카페 수", f"{len(filtered)}곳")
    m2.metric("분포 시군구 수", f"{filtered['시군구명'].nunique()}개")
    m3.metric("최다 밀집 행정동", f"{dong_counts.index[0]} ({dong_counts.iloc[0]}곳)")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("시군구별 분포")
        st.bar_chart(region_counts)

    with c2:
        st.subheader("행정동별 상위 10곳")
        st.bar_chart(dong_counts.head(10))

    st.subheader("행정동별 집계표")
    summary = (
        filtered.groupby(["시군구명", "행정동명"])
        .size()
        .reset_index(name="스터디카페 수")
        .sort_values("스터디카페 수", ascending=False)
        .reset_index(drop=True)
    )
    summary["비율(%)"] = (summary["스터디카페 수"] / len(filtered) * 100).round(1)
    st.dataframe(summary, width="stretch", hide_index=True)
