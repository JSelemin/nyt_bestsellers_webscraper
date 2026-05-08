[![es](https://img.shields.io/badge/lang-es-yellow.svg)](https://github.com/JSelemin/nyt_bestsellers_webscraper/blob/main/README.md)

# NYT Best Sellers Data Pipeline
 
Web scraping pipeline that collects 3 years of weekly NYT Best Sellers data using BeautifulSoup and requests, with MD5 hashing to deduplicate books across 150+ weekly snapshots. It laters loads the data into a star schema in SQLite and connects it to Power BI, enabling rank trajectory analysis, author frequency trends, and list longevity visualizations.
 
## What This Project Does
 
Every week, the New York Times publishes its Best Sellers list for fiction and non-fiction. This pipeline collects 156 weeks of that data (2023–2026), cleans and deduplicates it, and loads it into a star schema database. The resulting dataset tracks which books appeared on the list, when, at what rank, and for how long — enabling analysis of list dynamics over time.
 
## Tech Stack
 
- Python
- MS Power BI
- requests
- BeautifulSoup
- pandas
- SQLite
 
## Pipeline Architecture
 
```
NYTimes Best Sellers (HTML)
        ↓
    scraper.py       ← requests + BeautifulSoup, one week at a time
                       rate-limited (1.5s/request), error-handled per week
        ↓
  pandas DataFrames  ← MD5 hash deduplication, null handling for missing links
        ↓
    loader.py        ← explicit SQLite schema, INSERT OR IGNORE
        ↓
  bestsellers.db     ← dim_books + fact_rankings
        ↓
  Power BI (ODBC)    ← dashboards and analysis
```

## Schema
 
The database uses a simple star schema with one dimension table and one fact table.
 
```sql
CREATE TABLE IF NOT EXISTS books (
    hash_id         TEXT PRIMARY KEY,   -- MD5(title|author)
    title           TEXT,
    author          TEXT,
    upc             TEXT,               -- ISBN-13, nullable (not all books have Apple Books links)
    bookshop_url    TEXT
);
 
CREATE TABLE IF NOT EXISTS rankings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    hash_id     TEXT NOT NULL REFERENCES books(hash_id),
    date        TEXT NOT NULL,
    rank        INTEGER NOT NULL,
    UNIQUE(hash_id, week_date)          -- prevents duplicates on re-run
);
```
 
#### Key design decisions

- `hash_id` is derived from `MD5(title|author)` rather than a scraped identifier. This ensures a book is treated as the same entity across all 156 weeks regardless of minor scraping inconsistencies or books belonging to sagas.
- UPC lives only in `books`, not in `rankings` — it is a book attribute, not a ranking event attribute.
- `INSERT OR IGNORE` combined with the `UNIQUE` constraint on `(hash_id, week_date)` makes the loader idempotent — safe to re-run without creating duplicates.

## Setup
 
**Requirements**

```
pip install requirements.txt
```
 
**Run the pipeline**

```bash
python main.py
```
 
This runs scraper → transform → loader in sequence. Expect roughly 10 minutes for the full 3-year backfill due to rate limiting. Progress is printed per week.
 
**Connect to Power BI**
1. Install the SQLite ODBC driver and load the database in `data/NYT_bestsellers.db`
2. In Power BI Desktop: Get Data → ODBC → point to the database
3. Load both tables and define the relationship on `hash_id` if Power BI doesn't do it automatically
 
## Findings
 
**Longevity requires sustained performance.** Books with 40+ weeks on the list consistently averaged between rank 4 and rank 9. No long-running book had an average rank worse than 10, suggesting that books which fall to the bottom of the list tend to exit quickly rather than linger.
 
**Two distinct dominance strategies emerged.** *The Housemaid* (Freida McFadden) entered at rank 14 in November 2023 and became the longest-running title in the dataset — 124 weeks with an average rank of 9, sustained by gradual climb rather than immediate impact. Danielle Steel, by contrast, placed ~20 distinct titles on the list over the same period, dominating through volume rather than individual book longevity.
 
## Limitations
 
- **CSS selector fragility**: the scraper targets auto-generated class names (e.g. `css-1u6k25n`) which will break if NYT updates their frontend. A more robust approach would use structural selectors (e.g. `article:nth-child`) or monitor for selector changes.
- **Single list**: the pipeline currently targets combined print and e-book fiction only. The schema could support multiple lists via a `list_name` column, extending to nonfiction or genre lists with minimal changes.
- **Incremental updates**: the current pipeline does a full historical backfill. Adding a `pipeline_metadata` table to track the last loaded week would make it re-runnable on a weekly schedule (cron or Task Scheduler).
- **Scheduling**: unscheduled for now. A production version would run weekly.