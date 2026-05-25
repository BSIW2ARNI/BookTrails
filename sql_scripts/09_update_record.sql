-- Выполнение запроса на редактирование данных
-- Пример: изменение параметров уведомления
-- Параметры:
--   :notification_id - идентификатор уведомления
--   :title           - новый заголовок
--   :text            - новый текст
--   :kind            - новый тип уведомления
--   :is_read         - статус прочтения (0 или 1)

UPDATE web_notification
SET
    title = :title,
    text = :text,
    kind = :kind,
    is_read = :is_read
WHERE id = :notification_id;
