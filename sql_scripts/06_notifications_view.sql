-- Выполнение запроса на просмотр уведомлений
-- Параметры:
--   :user_id    - идентификатор пользователя
--   :limit_rows - ограничение по числу записей

SELECT
    n.id,
    n.kind,
    n.title,
    n.text,
    n.is_read,
    n.created_at
FROM web_notification AS n
WHERE n.user_id = :user_id
ORDER BY n.created_at DESC
LIMIT :limit_rows;
