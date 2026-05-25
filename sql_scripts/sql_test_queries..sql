-- Поиск и просмотр информации в каталоге
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
WHERE ('Роман' IS NULL OR b.genre = 'Роман')
  AND ('Русский' IS NULL OR b.language = 'Русский')
GROUP BY
    b.id, b.title, b.authors, b.genre, b.language, b.year,
    b.description, b.cover, b.accent, b.isbn, b.created_at
ORDER BY b.title ASC;


-- Просмотр подробной информации о книге
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
WHERE b.id = 1
GROUP BY
    b.id, b.title, b.authors, b.genre, b.language, b.year,
    b.description, b.cover, b.accent, b.isbn, b.created_at,
    c.id, c.code, c.status, c.created_at, u.display_name
ORDER BY c.created_at DESC;


-- Просмотр истории перемещений экземпляра
SELECT
    m.id,
    m.event_type,
    m.date_time,
    m.place_text,
    m.text,
    m.source,
    c.id AS copy_id,
    c.code AS copy_code,
    b.id AS book_id,
    b.title AS book_title,
    u.display_name AS user_name,
    t.uid AS nfc_tag_uid,
    s.id AS scan_id
FROM web_move AS m
INNER JOIN web_copy AS c
    ON c.id = m.copy_id
INNER JOIN web_book AS b
    ON b.id = c.book_id
LEFT JOIN web_btuser AS u
    ON u.id = m.user_id
LEFT JOIN web_nfctag AS t
    ON t.id = m.nfc_tag_id
LEFT JOIN web_nfcscan AS s
    ON s.id = m.scan_id
WHERE m.copy_id = 1
ORDER BY m.date_time DESC;


-- Просмотр и фильтрация событий
SELECT
    m.id,
    m.event_type,
    m.date_time,
    m.place_text,
    m.text,
    m.source,
    c.id AS copy_id,
    c.code AS copy_code,
    b.id AS book_id,
    b.title AS book_title,
    u.display_name AS user_name
FROM web_move AS m
INNER JOIN web_copy AS c
    ON c.id = m.copy_id
INNER JOIN web_book AS b
    ON b.id = c.book_id
LEFT JOIN web_btuser AS u
    ON u.id = m.user_id
WHERE ('Передача' IS NULL OR m.event_type = 'Передача')
ORDER BY m.date_time DESC
LIMIT 20 OFFSET 0;


-- Вывод персональных рекомендаций
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
WHERE rec.user_id = 1
ORDER BY rec.score DESC, rec.created_at DESC
LIMIT 10;


-- Просмотр уведомлений
SELECT
    n.id,
    n.kind,
    n.title,
    n.text,
    n.is_read,
    n.created_at
FROM web_notification AS n
WHERE n.user_id = 1
ORDER BY n.created_at DESC
LIMIT 15;


-- Формирование профиля пользователя: основные данные
SELECT
    u.id,
    u.email,
    u.display_name,
    u.avatar,
    u.status,
    u.privacy,
    u.is_active,
    u.created_at,
    u.updated_at
FROM web_btuser AS u
WHERE u.id = 1;


-- Формирование профиля пользователя: статистика
SELECT
    (SELECT COUNT(*) FROM web_copy WHERE initiator_id = 1) AS tracked_books,
    (SELECT COUNT(*) FROM web_review WHERE author_id = 1) AS reviews_count,
    (SELECT COUNT(*) FROM web_move WHERE user_id = 1) AS events_logged;


-- Формирование профиля пользователя: активные сессии
SELECT
    s.id,
    s.device,
    s.location,
    s.last_seen,
    s.created_at,
    s.current
FROM web_authsession AS s
WHERE s.user_id = 1
  AND s.revoked = 0
ORDER BY s.created_at DESC;


-- Формирование профиля пользователя: последние отзывы
SELECT
    r.id,
    r.rating,
    r.text,
    r.moderation_status,
    r.created_at,
    b.id AS book_id,
    b.title AS book_title
FROM web_review AS r
INNER JOIN web_book AS b
    ON b.id = r.book_id
WHERE r.author_id = 1
ORDER BY r.created_at DESC
LIMIT 2;


-- Добавление новой записи
INSERT INTO web_review (
    rating,
    text,
    moderation_status,
    created_at,
    author_id,
    book_id
)
VALUES (
    5,
    'Сильное впечатление от книги, рекомендую к прочтению.',
    'Опубликован',
    CURRENT_TIMESTAMP,
    1,
    1
);


-- Редактирование данных
UPDATE web_notification
SET
    title = 'Обновление маршрута книги',
    text = 'Экземпляр был передан новому читателю.',
    kind = 'Событие',
    is_read = 1
WHERE id = 1;


-- Удаление записи
DELETE FROM web_notification
WHERE id = 1;
