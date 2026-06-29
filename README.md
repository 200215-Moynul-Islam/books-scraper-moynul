# Books Scraper – Enterprise Web Scraping Pipeline

A production-ready Scrapy application that scrapes book data from [books.toscrape.com](https://books.toscrape.com), processes it through a pipeline, exports it in multiple formats, and stores it in SQLite — fully containerized with Docker and deployable via Scrapyd.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation Guide](#installation-guide)
- [Environment Setup](#environment-setup)
- [Running the Spider](#running-the-spider)
- [Docker Setup Guide](#docker-setup-guide)
- [Scrapyd Deployment Guide](#scrapyd-deployment-guide)
- [Output Format Description](#output-format-description)
- [Database Configuration](#database-configuration)
- [Architecture Diagram](#architecture-diagram)
- [Folder Structure](#folder-structure)
- [Design Decisions](#design-decisions)
- [Known Limitations](#known-limitations)

---

## Project Overview

This project implements a complete web scraping pipeline for the Books to Scrape demo website. The spider dynamically discovers all book categories, randomly selects 5 categories, then randomly selects 5 books from each selected category, extracts structured data, and routes it through a cleaning pipeline before writing to SQLite and exporting to JSON, CSV, and XML.

---

## Features

- Dynamically discovers all book categories — no hardcoded category names or URLs
- Randomly selects 5 categories from all discovered categories
- Handles multi-page category listings via recursive pagination
- Randomly selects exactly 5 books from each selected category
- Cleans and normalizes all extracted fields through an item pipeline
- Exports data to JSON, CSV, and XML via Scrapy Feed Exports
- Stores all records in SQLite through a dedicated pipeline
- Fully containerized with Docker
- Deployable and executable via Scrapyd API

---

## Tech Stack

| Component        | Technology        |
| ---------------- | ----------------- |
| Scraping         | Scrapy 2.16       |
| Language         | Python 3.12       |
| Database         | SQLite (built-in) |
| Deployment       | Scrapyd 1.6       |
| Containerization | Docker            |

---

## Installation Guide

### Prerequisites

- Python 3.12+
- pip
- Docker (for containerized runs)

### Steps

```bash
# Clone the repository
git clone https://github.com/200215-Moynul-Islam/books-scraper-moynul.git
cd books-scraper-moynul

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Environment Setup

By default, the database is named `books.db`. To use a different name, update `DATABASE_NAME` in `settings.py`:

```python
DATABASE_NAME = "books.db"
```

Output file paths are configured in `settings.py` under `FEEDS`. By default, files are exported to the `output/` directory. To change the paths or formats, update the `FEEDS` dictionary:

```python
FEEDS = {
    "output/books.json": {"format": "json", "indent": 4},
    "output/books.csv":  {"format": "csv"},
    "output/books.xml":  {"format": "xml"},
}
```

---

## Running the Spider

```bash
# From the project root with the virtual environment active:
scrapy crawl books
```

This will:

1. Discover all categories on the homepage dynamically
2. Randomly select 5 categories from the discovered list
3. Crawl all pages within each selected category
4. Randomly select 5 books from each category's full book pool
5. Clean and process each item
6. Write output to `output/books.json`, `output/books.csv`, `output/books.xml`
7. Insert all records into `books.db`

---

## Docker Setup Guide

The application is fully containerized. Scrapyd runs inside the container and exposes port `6800`.

### Build the image

```bash
docker build -t books-scraper .
```

### Run the container

```bash
docker run -d -p 6800:6800 --name books-scraper books-scraper
```

Scrapyd will be running and accessible at `http://localhost:6800`.

---

## Scrapyd Deployment Guide

Scrapyd is a service for running Scrapy spiders. The spider can be deployed and executed via the Scrapyd API either with or without Docker.

### Without Docker

```bash
# Start Scrapyd in a separate terminal
scrapyd

# Deploy the project
scrapyd-deploy
```

### With Docker

Ensure the Docker container is running (see [Docker Setup Guide](#docker-setup-guide)), then deploy from within the container:

```bash
docker exec -it books-scraper scrapyd-deploy
```

### 1. Schedule a crawl via the API

```bash
curl http://localhost:6800/schedule.json \
  -d project=books_scraper \
  -d spider=books
```

### 2. Check job status

```bash
curl http://localhost:6800/listjobs.json?project=books_scraper
```

### 3. View running spiders

```bash
curl http://localhost:6800/daemonstatus.json
```

### Browser Access

Scrapyd also provides a web UI. Once running, open your browser and navigate to:

```
http://localhost:6800
```

From there you can view scheduled, running, and finished jobs.

### Scrapyd configuration (`scrapyd.conf`)

```ini
[scrapyd]
bind_address = 0.0.0.0
http_port    = 6800
max_proc     = 4
```

---

## Output Format Description

All three export formats contain the same fields:

| Field          | Type    | Description                                       |
| -------------- | ------- | ------------------------------------------------- |
| `title`        | string  | Book title, whitespace stripped                   |
| `price`        | float   | Price with currency symbol removed (e.g. `13.12`) |
| `availability` | boolean | `true` if in stock, `false` otherwise             |
| `product_url`  | string  | Relative URL to the book's detail page            |
| `image_url`    | string  | Relative URL to the book's cover image            |
| `category`     | string  | Category name, whitespace stripped                |

### Sample JSON record

```json
{
  "title": "A Study in Scarlet (Sherlock Holmes #1)",
  "price": 16.73,
  "availability": true,
  "product_url": "../../../a-study-in-scarlet-sherlock-holmes-1_656/index.html",
  "image_url": "../../../../media/cache/8f/a4/8fa41d6caa10e427356b8a590eb4d96b.jpg",
  "category": "Mystery"
}
```

---

## Database Configuration

The project uses SQLite with no additional setup required. The database file `books.db` is created automatically in the project root when the spider runs.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     BooksSpider                         │
│                                                         │
│  start_urls ──► parse()                                 │
│                   │                                     │
│                   ▼                                     │
│           Discover all categories                       │
│           (CSS: .nav>li>ul>li>a)                        │
│                   │                                     │
│          Random sample: 5 categories                    │
│                   │                                     │
│                   ▼                                     │
│           parse_category()  ◄──────────────┐            │
│                   │                        │            │
│          Collect all books on page         │            │
│                   │                        │            │
│          Next page? ───── YES ─────────────┘            │
│                   │                                     │
│                  NO                                     │
│                   │                                     │
│          Random sample: 5 books                         │
│                   │                                     │
│                   ▼                                     │
│              yield BookItem                             │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                  Item Pipeline                          │
│                                                         │
│  CleanBookDataPipeline (priority 100)                   │
│    ├── Strip whitespace from title, category            │
│    ├── Strip currency symbol, cast price to float       │
│    └── Normalize availability to boolean                │
│                                                         │
│  SQLitePipeline (priority 300)                          │
│    └── INSERT into books table                          │
└───────────────────┬─────────────────────────────────────┘
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
   Feed Exports            SQLite DB
   ├── books.json          books.db
   ├── books.csv
   └── books.xml
```

---

## Folder Structure

```
books-scraper-moynul/
├── books_scraper/
│   ├── spiders/
│   │   ├── __init__.py
│   │   └── books.py          # Main spider
│   ├── __init__.py
│   ├── items.py              # BookItem definition
│   ├── middlewares.py        # Spider and downloader middlewares
│   ├── pipelines.py          # CleanBookDataPipeline + SQLitePipeline
│   └── settings.py           # All project settings, feeds, pipelines
├── output/
│   ├── .gitkeep
│   ├── books.json            # Generated on run
│   ├── books.csv             # Generated on run
│   └── books.xml             # Generated on run
├── Dockerfile
├── scrapyd.conf
├── scrapy.cfg
├── setup.py
├── requirements.txt
├── .dockerignore
├── .gitignore
└── README.md
```

---

## Design Decisions

**Separation of concerns via pipelines** — Data cleaning (`CleanBookDataPipeline`) and persistence (`SQLitePipeline`) are separate classes with distinct pipeline priorities. This keeps each class focused on one responsibility and makes it easy to swap out the database or add new cleaning steps without touching unrelated code.

**No hardcoded categories or URLs** — The spider extracts all category links dynamically from the site's navigation on every run. If the site adds or removes categories, no code changes are needed.

**Pagination handled recursively with accumulated state** — Books are collected across all pages of a category before the 5-book sample is taken. This ensures the random sample is drawn from the complete pool, not just the first page.

---

## Known Limitations

- **Not all categories are scraped** — The spider randomly samples 5 categories per run rather than scraping all available categories. Books from unselected categories are never fetched.

- **Not all books per category are collected** — Only 5 randomly selected books are collected from each selected category. The remaining books in that category are not scraped.

- **SQLite only** — The current implementation supports SQLite. MongoDB support is not included but can be added as an additional pipeline class without modifying existing code.

- **Output files are overwritten on each run** — Scrapy's feed exporter will overwrite existing output files. Previous run data is not preserved unless you rename or back up the files.
