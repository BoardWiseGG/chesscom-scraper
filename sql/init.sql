CREATE SCHEMA IF NOT EXISTS coach_scraper;

DROP TABLE IF EXISTS coach_scraper.export;

CREATE TABLE coach_scraper.export
  ( id SERIAL PRIMARY KEY
  , site VARCHAR(16) NOT NULL
  , username VARCHAR(255) NOT NULL
  , name VARCHAR(255)
  , image_url TEXT
  , languages TEXT[]
  , title VARCHAR(3)
  , rapid INT
  , blitz INT
  , bullet INT
  , position INT
  );

CREATE UNIQUE INDEX IF NOT EXISTS
  site_username_unique
ON
  coach_scraper.export
USING
  BTREE (site, username);

DROP TABLE IF EXISTS coach_scraper.languages;

CREATE TABLE coach_scraper.languages
  ( id SERIAL PRIMARY KEY
  , code VARCHAR(8) NOT NULL
  , name VARCHAR(128) NOT NULL
  , pos INTEGER NOT NULL
  );

CREATE UNIQUE INDEX IF NOT EXISTS
  code_unique
ON
  coach_scraper.languages
USING
  BTREE (code);
