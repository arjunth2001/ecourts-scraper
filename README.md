# ecourts-scraper

Scrapes the e-courts website to download case judgements

## Steps:-

- Set start date, end date, base dir, base url, start index, end index in chunker.py
- install all requirements
- move chrome driver to this directory
- needs chrome installed
- run `python chunker.py`
- Implements multiprocessing. Enjoy!

You can run all districts but keep time span small to avoid timeout within a district. Each court is a new session.
