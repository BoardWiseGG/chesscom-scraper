DO $$
  BEGIN
    EXECUTE format(
      'CREATE TABLE coach_scraper.export_%s AS TABLE coach_scraper.export',
      TRUNC(EXTRACT(EPOCH FROM CURRENT_TIMESTAMP), 0)
    );
  END;
$$ LANGUAGE plpgsql;

CREATE TEMPORARY TABLE pg_temp.coach_scraper_export (data JSONB);

SELECT format(
  $$COPY pg_temp.coach_scraper_export (data) from %L$$,
  :export
) \gexec

INSERT INTO coach_scraper.export
  ( username
  , site
  , rapid
  , blitz
  , bullet
  )
SELECT
  data->>'username',
  data->>'site',
  (data->>'rapid')::INT,
  (data->>'blitz')::INT,
  (data->>'bullet')::INT
FROM
  pg_temp.coach_scraper_export
ON CONFLICT
  (site, username)
DO UPDATE SET
  rapid = EXCLUDED.rapid,
  blitz = EXCLUDED.blitz,
  bullet = EXCLUDED.bullet;
