-- 1) Paste the FULL contents of questions.json between $$ ... $$ below
WITH raw AS (
    SELECT
        $$[
          -- paste your JSON array from questions.json here
        ]$$::jsonb AS data
),

-- 2) Turn JSON array into one row per question
q AS (
    SELECT jsonb_array_elements(raw.data) AS item
    FROM raw
)

-- 3) Insert into questions table
INSERT INTO questions (question_text, question_type, order_index)
SELECT
    item->>'text'        AS question_text,
    item->>'type'        AS question_type,
    (item->>'id')::int   AS order_index
FROM q
ON CONFLICT (order_index) DO UPDATE
SET
    question_text = EXCLUDED.question_text,
    question_type = EXCLUDED.question_type;
