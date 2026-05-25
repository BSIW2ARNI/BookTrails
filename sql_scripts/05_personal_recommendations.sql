-- Выполнение запроса на вывод персональных рекомендаций
-- Параметры:
--   :user_id    - идентификатор пользователя
--   :limit_rows - ограничение по числу записей

SELECT
    rec.id,
    rec.score,
    rec.explanation,
    rec.created_at,
    b.id AS book_id,
    b.title,
    b.authors,
    b.genre,
    b.language,
    b.year,
    b.cover,
    b.accent
FROM web_recommendation AS rec
INNER JOIN web_book AS b
    ON b.id = rec.book_id
WHERE rec.user_id = :user_id
ORDER BY rec.score DESC, rec.created_at DESC
LIMIT :limit_rows;
