import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_URL = "https://raw.githubusercontent.com/happykth/data/main/kobis_movies.csv"

st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    layout="wide",
)


@st.cache_data(show_spinner="데이터를 불러오는 중입니다.")
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)

    # 개봉일: 여덟 자리 숫자(YYYYMMDD) -> 날짜형
    df["openDt"] = pd.to_datetime(
        df["openDt"].astype(str).str.strip(), format="%Y%m%d", errors="coerce"
    )

    # 장르: 세로막대(|)로 여러 개가 적힌 경우 첫 번째 장르만 사용
    df["genre"] = (
        df["genre"]
        .fillna("미분류")
        .astype(str)
        .str.split("|")
        .str[0]
        .str.strip()
        .replace("", "미분류")
    )

    # 수치형 열 정리
    num_cols = [
        "first_scrn",
        "first_show",
        "first_week_audi",
        "total_audi",
        "days_in_top10",
    ]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def insight_section(placeholder: str = "여기에 이 그래프로 알 수 있는 내용을 한 문장으로 적어 주십시오.") -> None:
    """그래프 아래에 '이 그래프로 알 수 있는 것' 한 문장을 넣을 자리."""
    with st.container(border=True):
        st.markdown("**이 그래프로 알 수 있는 것**")
        st.markdown(f"_{placeholder}_")


# ---------------------------------------------------------------- 제목
st.title("영화 데이터 그래프 도감 2 - 분포와 관계")
st.caption("최근 1년간 박스오피스 10위권에 진입한 영화 중, 같은 기간에 개봉한 작품의 요약표를 바탕으로 합니다.")

try:
    movies = load_data(DATA_URL)
except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()

st.markdown(f"불러온 영화는 총 **{len(movies):,}편**입니다.")

st.divider()

# ---------------------------------------------------------------- 구역 1
st.header("1. 장르별 영화 편수")
st.markdown("영화별 첫 번째 장르를 기준으로 편수를 집계하였습니다.")

genre_counts = (
    movies["genre"]
    .value_counts()
    .rename_axis("genre")
    .reset_index(name="count")
)

fig_genre = go.Figure(
    go.Pie(
        labels=genre_counts["genre"],
        values=genre_counts["count"],
        hole=0.5,
        sort=False,  # 이미 편수 내림차순으로 정렬됨
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>편수: %{value}편<br>비율: %{percent}<extra></extra>",
    )
)
fig_genre.update_layout(
    margin=dict(t=20, b=20, l=20, r=20),
    legend_title_text="장르",
    annotations=[
        dict(
            text=f"전체<br>{len(movies):,}편",
            x=0.5,
            y=0.5,
            font_size=18,
            showarrow=False,
        )
    ],
)
st.plotly_chart(fig_genre, use_container_width=True)

insight_section()

st.divider()
