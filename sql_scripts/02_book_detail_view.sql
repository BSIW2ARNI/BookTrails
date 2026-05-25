-- Выполнение запроса на просмотр подробной информации о книге
-- Параметр:
--   :book_id - идентификатор книги

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
    COALESCE(AVG(r.rating), 0) AS average_rating,
    COUNT(DISTINCT r.id) AS reviews_count,
    c.id AS copy_id,
    c.code AS copy_code,
    c.status AS copy_status,
    c.created_at AS copy_created_at,
    u.display_name AS initiator_name
FROM web_book AS b
LEFT JOIN web_review AS r
    ON r.book_id = b.id
LEFT JOIN web_copy AS c
    ON c.book_id = b.id
LEFT JOIN web_btuser AS u
    ON u.id = c.initiator_id
WHERE b.id = :book_id
GROUP BY
    b.id, b.title, b.authors, b.genre, b.language, b.year,
    b.description, b.cover, b.accent, b.isbn, b.created_at,
    c.id, c.code, c.status, c.created_at, u.display_name
ORDER BY c.created_at DESC;
