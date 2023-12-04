DO $$
  BEGIN
    EXECUTE format(
      'CREATE TABLE coach_scraper.export_%s AS TABLE coach_scraper.export',
      TRUNC(EXTRACT(EPOCH FROM CURRENT_TIMESTAMP), 0)
    );
  END;
$$ LANGUAGE plpgsql;

-- This should match the order data is written in the app/__main__.py
-- script.
CREATE TEMPORARY TABLE pg_temp.coach_scraper_export
  ( site TEXT
  , username TEXT
  , name TEXT
  , image_url TEXT
  , rapid TEXT
  , blitz TEXT
  , bullet TEXT
  );

SELECT format(
  $$COPY pg_temp.coach_scraper_export FROM %L WITH (FORMAT CSV)$$,
  :export
) \gexec

INSERT INTO coach_scraper.export
  ( site
  , username
  , name
  , image_url
  , rapid
  , blitz
  , bullet
  )
SELECT
  site,
  username,
  name,
  image_url,
  rapid::INT,
  blitz::INT,
  bullet::INT
FROM
  pg_temp.coach_scraper_export
ON CONFLICT
  (site, username)
DO UPDATE SET
  name = EXCLUDED.name,
  image_url = EXCLUDED.image_url,
  rapid = EXCLUDED.rapid,
  blitz = EXCLUDED.blitz,
  bullet = EXCLUDED.bullet;
