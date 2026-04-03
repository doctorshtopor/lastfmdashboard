CREATE TABLE listenings(
    id INTEGER,
    Username TEXT,
    Artist TEXT,
    Track TEXT,
    Album TEXT,
    date DATE,
    time TIME
);


SELECT COUNT(*) AS total_plays -- 166153
FROM listenings 

SELECT COUNT(DISTINCT username) AS total_users -- 11
FROM listenings;

SELECT COUNT(DISTINCT Artist) AS total_artists
FROM listenings;

--задача 1: найти топ-5 исполнителей 
--по количеству прослушиваний
SELECT Artist, COUNT(*) AS artist_plays
FROM listenings
GROUP BY Artist
ORDER BY artist_plays DESC;

--задача: топ-10 самых прослушиваемых треков — 
--название трека, артист и количество прослушиваний. 
--Отсортировать по убыванию.

SELECT Artist,
       Track,
       COUNT(*) AS track_plays
FROM listenings
GROUP BY Track, Artist
ORDER BY track_plays DESC
LIMIT 10;
   
--задача 2:Вывести для каждого пользователя количество 
--прослушиваний и количество уникальных артистов 
--которых он слушал. Отсортировать по 
--количеству прослушиваний по убыванию.

SELECT Username,
       COUNT(*) AS user_plays,
       COUNT(DISTINCT Artist) AS amount_unique_artists
FROM listenings
GROUP BY Username
ORDER BY user_plays DESC;

--Задача 3. 
--Вывести для каждого пользователя его самого прослушиваемого артиста.


WITH artist_counts AS (
        SELECT Username,
           Artist,
           COUNT(*) AS artist_plays
        FROM listenings
        GROUP BY Username, Artist
        ORDER BY artist_plays DESC
    ),
ranked_artist_counts AS(
        SELECT Username,
            MAX(artist_plays) AS max_artist_plays
        FROM artist_counts
        GROUP BY Username
        ORDER BY max_artist_plays DESC
)
SELECT a.Username, a.Artist, a.artist_plays
FROM artist_counts AS a
JOIN ranked_artist_counts AS b 
ON a.Username = b.Username 
AND a.artist_plays = b.max_artist_plays
ORDER BY a.artist_plays DESC;

--Задача 4. Вывести для каждого дня и месяца количество прослушиваний.

SELECT COUNT(*) AS artist_plays,
       EXTRACT(DAY FROM date) AS day,
       EXTRACT(MONTH FROM date) AS month
FROM listenings
GROUP BY month, day
ORDER BY month, day;

--Задача 5. Вывести для каждого дня недели количество прослушиваний.

SELECT COUNT(*) AS artist_plays,
       EXTRACT(ISODOW FROM date) AS day_of_week
FROM listenings
GROUP BY day_of_week
ORDER BY day_of_week;


-- Задча 6. Сколько уникальных пользователей слушали каждого артиста?
SELECT Artist,
       COUNT(DISTINCT Username) AS unique_users
FROM listenings
GROUP BY Artist
HAVING COUNT(DISTINCT Username) >= 5
ORDER BY unique_users DESC

--Задача 7. для каждого пользователя 
--топ-5 артистов с их долей 
--от всех его прослушиваний в процентах.
 
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





