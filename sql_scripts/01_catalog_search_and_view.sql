-- Выполнение запроса на поиск и просмотр информации в каталоге
-- Параметры:
--   :genre     - жанр книги или NULL
--   :language  - язык книги или NULL

SELECT
    b.id,
    b.title,
    b.authors,
    b.genre,
    b.language,
    b.year,
    b.description,
    b.cover,
    b.accent,
    b.isbn,
    b.created_at,
    COALESCE(AVG(r.rating), 0) AS rating,
    COUNT(DISTINCT r.id) AS reviews_count
FROM web_book AS b
LEFT JOIN web_review AS r
    ON r.book_id = b.id
WHERE (:genre IS NULL OR b.genre = :genre)
  AND (:language IS NULL OR b.language = :language)
GROUP BY
    b.id, b.title, b.authors, b.genre, b.language, b.year,
    b.description, b.cover, b.accent, b.isbn, b.created_at
ORDER BY b.title ASC;
