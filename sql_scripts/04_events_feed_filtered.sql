-- Выполнение запроса на просмотр и фильтрацию событий
-- Параметры:
--   :event_type - тип события или NULL
--   :limit_rows - размер страницы
--   :offset_rows - смещение

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
WHERE (:event_type IS NULL OR m.event_type = :event_type)
ORDER BY m.date_time DESC
LIMIT :limit_rows OFFSET :offset_rows;


SELECT * FROM web_move



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