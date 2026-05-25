-- Выполнение запроса на удаление записи
-- Пример: удаление уведомления
-- Параметр:
--   :notification_id - идентификатор уведомления

DELETE FROM web_notification
WHERE id = :notification_id;
