import pandas as pd
import plotly.express as px
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

# ---------------------------------------------------------------- 구역 2
st.header("2. 장르별 영화 총 관객 트리맵")
st.markdown("칸의 크기는 영화별 총 관객 수에 비례하며, 각 영화는 소속 장르 안에 묶여 표시됩니다.")

treemap_df = movies.dropna(subset=["total_audi"])
treemap_df = treemap_df[treemap_df["total_audi"] > 0]

genres = list(treemap_df["genre"].unique())

# 영화명이 겹치거나 장르명과 같아도 섞이지 않도록 고유 id를 부여
fig_tree = go.Figure(
    go.Treemap(
        ids=[f"g:{g}" for g in genres] + [f"m:{c}" for c in treemap_df["movieCd"]],
        labels=genres + list(treemap_df["movieNm"]),
        parents=[""] * len(genres) + [f"g:{g}" for g in treemap_df["genre"]],
        values=[0] * len(genres) + list(treemap_df["total_audi"]),
        branchvalues="remainder",
        texttemplate="%{label}<br>%{value:,.0f}명",
        hovertemplate="<b>%{label}</b><br>총 관객: %{value:,.0f}명<extra></extra>",
    )
)
fig_tree.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=650)
st.plotly_chart(fig_tree, use_container_width=True)

insight_section()

st.divider()

# ---------------------------------------------------------------- 구역 3
st.header("3. 총 관객 수의 분포")
st.markdown("영화별 총 관객 수를 100만 명 단위 구간으로 나누어, 구간마다 영화가 몇 편인지 나타냈습니다.")

hist_df = movies.dropna(subset=["total_audi"])
BIN_SIZE = 1_000_000
edges = list(range(0, int(hist_df["total_audi"].max()) + BIN_SIZE + 1, BIN_SIZE))

fig_hist = go.Figure(
    go.Histogram(
        x=hist_df["total_audi"],
        xbins=dict(start=0, end=edges[-1], size=BIN_SIZE),
        hovertemplate="구간: %{x}명<br>영화: %{y}편<extra></extra>",
    )
)
fig_hist.update_layout(
    xaxis_title="총 관객 수(명)",
    yaxis_title="영화 편수",
    bargap=0.05,
    margin=dict(t=20, b=20, l=20, r=20),
)
fig_hist.update_xaxes(tickformat=",")
st.plotly_chart(fig_hist, use_container_width=True)

# 가장 영화가 많이 몰린 구간과 최다 관객 영화를 계산해 문구로 제시
bin_counts = pd.cut(hist_df["total_audi"], bins=edges, right=False).value_counts().sort_index()
top_bin = bin_counts.idxmax()
top_bin_n = int(bin_counts.max())
top_bin_share = top_bin_n / len(hist_df) * 100
best = hist_df.loc[hist_df["total_audi"].idxmax()]

with st.container(border=True):
    st.markdown("**이 그래프로 알 수 있는 것**")
    st.markdown(
        f"영화가 가장 많이 몰린 구간은 총 관객 **{int(top_bin.left) // 10000:,}만~{int(top_bin.right) // 10000:,}만 명**"
        f"({top_bin_n}편, 전체의 {top_bin_share:.1f}%)이며, "
        f"총 관객이 가장 많은 영화는 **{best['movieNm']}**({int(best['total_audi']):,}명)입니다."
    )

st.divider()

# ---------------------------------------------------------------- 구역 4
st.header("4. 개봉일 스크린수와 총 관객의 관계")
st.markdown("점 하나가 영화 한 편이며, 장르에 따라 색을 달리하였습니다.")

scatter_df = movies.dropna(subset=["first_scrn", "total_audi"])

fig_scatter = px.scatter(
    scatter_df,
    x="first_scrn",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    hover_data={"genre": True, "first_scrn": ":,", "total_audi": ":,"},
    labels={
        "first_scrn": "개봉일 스크린수(개)",
        "total_audi": "총 관객 수(명)",
        "genre": "장르",
    },
)
fig_scatter.update_traces(marker=dict(size=9, opacity=0.8))
fig_scatter.update_layout(margin=dict(t=20, b=20, l=20, r=20), legend_title_text="장르")
fig_scatter.update_yaxes(tickformat=",")
st.plotly_chart(fig_scatter, use_container_width=True)

insight_section()

st.divider()

# ---------------------------------------------------------------- 구역 5
MIN_MOVIES = 10

st.header("5. 장르별 총 관객의 분포")
st.markdown(f"영화가 {MIN_MOVIES}편 이상인 장르만 골라, 장르별 총 관객 수의 분포를 상자 그림으로 나타냈습니다.")

box_df = movies.dropna(subset=["total_audi"])
box_counts = box_df["genre"].value_counts()
box_genres = box_counts[box_counts >= MIN_MOVIES].index.tolist()  # 편수 많은 순
box_df = box_df[box_df["genre"].isin(box_genres)]

if not box_genres:
    st.info(f"영화가 {MIN_MOVIES}편 이상인 장르가 없습니다.")
else:
    fig_box = px.box(
        box_df,
        x="genre",
        y="total_audi",
        color="genre",
        points="outliers",  # 상자 밖으로 튀는 점만 표시
        hover_name="movieNm",
        hover_data={"genre": False, "total_audi": ":,"},
        category_orders={"genre": box_genres},
        labels={"genre": "장르", "total_audi": "총 관객 수(명)"},
    )
    fig_box.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
    fig_box.update_yaxes(tickformat=",")
    st.plotly_chart(fig_box, use_container_width=True)

insight_section()

st.divider()

# ---------------------------------------------------------------- 구역 6
st.header("6. 스크린수·총 관객·첫 주 관객의 관계")
st.markdown("네 번째 산점도에 점의 크기를 더하였습니다. 점이 클수록 개봉 첫 주 관객이 많은 영화입니다.")

bubble_df = movies.dropna(subset=["first_scrn", "total_audi", "first_week_audi"])
bubble_df = bubble_df[bubble_df["first_week_audi"] > 0]  # 크기가 0이면 점이 보이지 않으므로 제외

fig_bubble = px.scatter(
    bubble_df,
    x="first_scrn",
    y="total_audi",
    size="first_week_audi",
    color="genre",
    size_max=45,
    hover_name="movieNm",
    hover_data={
        "genre": True,
        "first_scrn": ":,",
        "total_audi": ":,",
        "first_week_audi": ":,",
    },
    labels={
        "first_scrn": "개봉일 스크린수(개)",
        "total_audi": "총 관객 수(명)",
        "first_week_audi": "개봉 첫 주 관객 수(명)",
        "genre": "장르",
    },
)
fig_bubble.update_traces(marker=dict(opacity=0.6, line=dict(width=0.5, color="white")))
fig_bubble.update_layout(margin=dict(t=20, b=20, l=20, r=20), legend_title_text="장르")
fig_bubble.update_yaxes(tickformat=",")
st.plotly_chart(fig_bubble, use_container_width=True)

insight_section()

st.divider()

# ---------------------------------------------------------------- 구역 7
st.header("7. 제작 국가와 장르의 구성")
st.markdown("안쪽 고리는 제작 국가, 바깥쪽 고리는 그 국가 영화의 장르이며, 칸의 크기는 영화 편수입니다.")

sun_df = movies.copy()
sun_df["nation"] = sun_df["nation"].fillna("미상").astype(str).str.strip().replace("", "미상")
sun_counts = sun_df.groupby(["nation", "genre"]).size().reset_index(name="count")

fig_sun = px.sunburst(
    sun_counts,
    path=["nation", "genre"],
    values="count",
)
fig_sun.update_traces(
    textinfo="label+value",
    hovertemplate="<b>%{label}</b><br>영화: %{value}편<br>상위 구성에서의 비율: %{percentParent:.1%}<extra></extra>",
)
fig_sun.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=650)
st.plotly_chart(fig_sun, use_container_width=True)

insight_section()

st.divider()
