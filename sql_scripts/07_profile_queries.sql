-- Выполнение запросов на формирование профиля пользователя
-- Параметр:
--   :user_id - идентификатор пользователя

-- 1. Основные данные профиля пользователя
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
WHERE u.id = :user_id;

-- 2. Агрегированная статистика по активности пользователя
SELECT
    (SELECT COUNT(*) FROM web_copy WHERE initiator_id = :user_id) AS tracked_books,
    (SELECT COUNT(*) FROM web_review WHERE author_id = :user_id) AS reviews_count,
    (SELECT COUNT(*) FROM web_move WHERE user_id = :user_id) AS events_logged;

-- 3. Активные сессии пользователя
SELECT
    s.id,
    s.device,
    s.location,
    s.last_seen,
    s.created_at,
    s.current
FROM web_authsession AS s
WHERE s.user_id = :user_id
  AND s.revoked = 0
ORDER BY s.created_at DESC;

-- 4. Последние отзывы пользователя
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
WHERE r.author_id = :user_id
ORDER BY r.created_at DESC
LIMIT 2;
