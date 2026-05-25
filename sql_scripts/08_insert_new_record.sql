-- Выполнение запроса на добавление новой записи
-- Пример: добавление нового отзыва к книге
-- Параметры:
--   :book_id            - идентификатор книги
--   :author_id          - идентификатор автора отзыва
--   :rating             - числовая оценка
--   :text               - текст отзыва
--   :moderation_status  - статус модерации

INSERT INTO web_review (
    rating,
    text,
    moderation_status,
    created_at,
    author_id,
    book_id
)
VALUES (
    :rating,
    :text,
    :moderation_status,
    CURRENT_TIMESTAMP,
    :author_id,
    :book_id
);
