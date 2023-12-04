CREATE SCHEMA IF NOT EXISTS coach_scraper;

DROP TABLE IF EXISTS coach_scraper.export;

CREATE TABLE coach_scraper.export
  ( id SERIAL PRIMARY KEY
  , site VARCHAR(16) NOT NULL
  , username VARCHAR(255) NOT NULL
  , name VARCHAR(255)
  , image_url TEXT
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
