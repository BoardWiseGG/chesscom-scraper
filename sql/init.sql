CREATE SCHEMA IF NOT EXISTS coach_scraper;

CREATE TABLE IF NOT EXISTS coach_scraper.export
  ( id SERIAL PRIMARY KEY
  , username VARCHAR(255) NOT NULL
  , site VARCHAR(16) NOT NULL
  , rapid INT
  , blitz INT
  , bullet INT
  );

CREATE UNIQUE INDEX IF NOT EXISTS
  site_username_unique
ON
  coach_scraper.export
USING
  BTREE (site, username);

DO $$
  BEGIN
    IF NOT EXISTS (
      SELECT 1
      FROM information_schema.constraint_column_usage 
      WHERE table_schema = 'coach_scraper'
      AND table_name = 'export'
      AND constraint_name = 'site_username_unique'
    ) THEN
      EXECUTE 'ALTER TABLE
        coach_scraper.export
      ADD CONSTRAINT
        site_username_unique
      UNIQUE USING INDEX
        site_username_unique';
    END IF;
  END;
$$ LANGUAGE plpgsql;
