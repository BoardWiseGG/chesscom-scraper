CREATE SCHEMA IF NOT EXISTS coach_scraper;

DO $$
  BEGIN
    EXECUTE format(
      'ALTER TABLE IF EXISTS coach_scraper.export '
      'RENAME TO export_%s;',
      TRUNC(EXTRACT(EPOCH FROM CURRENT_TIMESTAMP), 0)
    );
  END;
$$ LANGUAGE plpgsql;

CREATE TABLE coach_scraper.export
  ( username VARCHAR(255) NOT NULL
  , site VARCHAR(16) NOT NULL
  , rapid INT
  , blitz INT
  , bullet INT
  );

CREATE TEMPORARY TABLE pg_temp.coach_scraper_export (data JSONB);

SELECT format(
  $$COPY pg_temp.coach_scraper_export (data) from %L$$,
  :export
) \gexec

INSERT INTO coach_scraper.export
SELECT
  data->>'username',
  data->>'site',
  (data->>'rapid')::INT,
  (data->>'blitz')::INT,
  (data->>'bullet')::INT
FROM
  pg_temp.coach_scraper_export;
