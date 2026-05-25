-- Выполнение запроса на просмотр истории перемещений экземпляра
-- Параметр:
--   :copy_id - идентификатор экземпляра

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
WHERE m.copy_id = :copy_id
ORDER BY m.date_time DESC;
