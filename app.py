import streamlit as st
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))

st.title("Last.fm Dashboard")

# получаем данные из БД
df = pd.read_sql("SELECT COUNT(*) AS total_plays FROM listenings", conn)

# вытаскиваем конкретное число из датафрейма
total_plays = df["total_plays"][0]


du = pd.read_sql("SELECT COUNT(DISTINCT username) AS total_users FROM listenings;", conn)

total_users = du["total_users"][0]

da = pd.read_sql(
    "SELECT COUNT(DISTINCT Artist) AS total_artists FROM listenings;", conn
)

total_artists = da["total_artists"][0]

#метрики:
col1, col2, col3 = st.columns(3)
col1.metric("Всего прослушиваний", total_plays)
col2.metric("Всего пользователей", total_users)
col3.metric("Всего артистов", total_artists)

import plotly.express as px

st.subheader("Топ-10 исполнителей")

df_artists = pd.read_sql("""
    SELECT Artist, COUNT(*) AS plays
    FROM listenings
    GROUP BY Artist
    ORDER BY plays DESC
    LIMIT 10
""", conn)

fig = px.bar(df_artists, x="plays", y="artist", orientation="h",
             category_orders={"artist": df_artists["artist"].tolist()},
             labels={"artist": "", "plays": "Прослушиваний"})
st.plotly_chart(fig)

st.subheader("Топ-10 композиций")

df_tracks = pd.read_sql("""
    SELECT Artist, Track, COUNT(*) AS track_plays
    FROM listenings
    GROUP BY Track, Artist
    ORDER BY track_plays DESC
    LIMIT 10;
""", conn)

df_tracks["label"] = df_tracks["artist"] + " — " + df_tracks["track"]

fig = px.bar(df_tracks, x="track_plays", y="label", orientation="h",
             category_orders={"track": df_tracks["track"].tolist()},
             labels={"label": "", "track_plays": "Прослушиваний"},
             hover_data=["artist"])
st.plotly_chart(fig)

st.subheader("Профиль пользователей")

df_users = pd.read_sql("""
    SELECT Username, COUNT(*) AS user_plays,
           COUNT(DISTINCT Artist) AS amount_unique_artists
    FROM listenings
    GROUP BY Username
    ORDER BY user_plays DESC
""", conn)

df_top_artist = pd.read_sql("""
    WITH artist_counts AS (
        SELECT Username, Artist, COUNT(*) AS artist_plays
        FROM listenings
        GROUP BY Username, Artist
    ),
    max_plays AS (
        SELECT Username, MAX(artist_plays) AS max_artist_plays
        FROM artist_counts
        GROUP BY Username
    )
    SELECT a.Username, a.Artist AS top_artist
    FROM artist_counts a
    JOIN max_plays b ON a.Username = b.Username 
        AND a.artist_plays = b.max_artist_plays
""", conn)

# объединяем два датафрейма по Username
df_merged = pd.merge(df_users, df_top_artist, on="username")

st.dataframe(
    df_merged.rename(columns={
        "username": "Пользователь",
        "user_plays": "Прослушиваний",
        "amount_unique_artists": "Уникальных артистов",
        "top_artist": "Любимый артист"
    }),
    hide_index=True,
    use_container_width=True
)

st.subheader('Дневная активность')

df_day_activity = pd.read_sql("""
SELECT COUNT(*) AS artist_plays,
       EXTRACT(DAY FROM date) AS day,
       EXTRACT(MONTH FROM date) AS month
FROM listenings
GROUP BY month, day
ORDER BY month, day;
""", conn)

fig = px.line(df_day_activity, x="day", y="artist_plays", orientation="h",
             category_orders={"artist_plays": df_day_activity["artist_plays"].tolist()},
             labels={"day": "День", "artist_plays": "Прослушиваний"})
st.plotly_chart(fig)
st.caption("⚠️ 31 января — скорее всего, артефакт датасета: прослушиваний колоссально много, так как часть записей при экспорте с Last.fm получила одну и ту же дату")


df_days = pd.read_sql("""
SELECT COUNT(*) AS artist_plays,
       EXTRACT(ISODOW FROM date) AS day_of_week
FROM listenings
GROUP BY day_of_week
ORDER BY day_of_week;
""", conn)

days_map = {1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб", 7: "Вс"}
df_days["day_name"] = df_days["day_of_week"].map(days_map)

fig = px.bar(df_days, x="day_name", y="artist_plays", orientation="v",
             category_orders={"artist_plays": df_days["artist_plays"].tolist()},
             labels={"day_name": "День", "artist_plays": "Прослушиваний"})
st.plotly_chart(fig)

st.subheader("Популярные артисты среди аудитории")

df_popular = pd.read_sql("""
SELECT Artist,
       COUNT(DISTINCT Username) AS unique_users
FROM listenings
GROUP BY Artist
HAVING COUNT(DISTINCT Username) >= 5
ORDER BY unique_users DESC
""", conn)

fig = px.bar(df_popular, x="unique_users", y="artist", orientation="h",
             color="unique_users",
             color_continuous_scale="blues",
             category_orders={"artist": df_popular.sort_values("unique_users")["artist"].tolist()},
             labels={"artist": "", "unique_users": "Уникальные пользователи"})
fig.update_layout(coloraxis_showscale=False)
st.plotly_chart(fig, key="popular_artists")

st.subheader("Топ-5 артистов пользователя")

df_shares = pd.read_sql("""
    WITH artist_counts AS(
    SELECT SUM(artist_plays) OVER (PARTITION BY Username) AS total_plays_per_user,
       Artist,
       Username,
       artist_plays,
       ROUND((artist_plays::DECIMAL / SUM(artist_plays) OVER (PARTITION BY Username)) * 100, 2) AS percentage_of_total_plays,
       ROW_NUMBER() OVER (PARTITION BY Username ORDER BY artist_plays DESC) AS rank
    FROM (
       SELECT Username,
           Artist,
           COUNT(*) AS artist_plays
       FROM listenings
       GROUP BY Username, Artist
    ) AS artist_counts
    ORDER BY Username, artist_plays DESC
)
SELECT * FROM artist_counts
WHERE rank <= 5
ORDER BY Username, rank;
""", conn)

df_shares = df_shares[df_shares["rank"] <= 5]

user = st.selectbox("Выбери пользователя", df_shares["username"].unique())

df_user = df_shares[df_shares["username"] == user]

fig = px.pie(df_user, values="percentage_of_total_plays", names="artist",
             title=f"Топ-5 артистов — {user}")
st.plotly_chart(fig, key="pie_chart")
