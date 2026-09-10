# Yahoo Finance Scraping Dashboard

A stock dashboard that pulls its data from Yahoo Finance. The Django backend
scrapes prices, company info, historical data and news for a ticker, saves it
into a SQLite database, and serves it over a REST API. The React frontend reads
from that API and shows everything as a dashboard with a price chart.

## Live links

- Dashboard: https://yahoo-dashboard-theta.vercel.app/
- API: https://yahoo-dashboard-phr0.onrender.com/api/tickers/
- Source-code: https://github.com/Shubham-design472/yahoo-dashboard

One thing to know: the backend runs on Render's free plan, which puts the
service to sleep after about 15 minutes with no traffic. The first request
after it sleeps takes 30-60 seconds to wake up. After that it's fast.

## Tech I used

The backend is Django with Django REST Framework. The frontend is React (built
with Vite), using React Router for the two pages and Recharts for the price
chart. The database is SQLite. For the scraping I used the requests library.
The backend is deployed on Render and the frontend on Vercel, both free tiers.

I kept the scraping and the API in separate Django apps. The `scraper` app has
all the network and parsing logic plus the scrape command, and the `stocks` app
has the models, serializers and API views.

```
yahoo-dashboard/
├── backend/
│   ├── config/        settings and root URLs
│   ├── stocks/        models, serializers, API views
│   ├── scraper/       Yahoo client, parsers, and the scrape command
│   ├── tickers.json   seed ticker list
│   ├── seed_data.json data exported from a local scrape, used to seed on deploy
│   └── requirements.txt
└── frontend/
    └── src/           React pages, components, the API helper and styles
```

## Running it locally

Backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate          # on Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py scrape --all     # scrape the seed tickers
python manage.py createsuperuser  # optional, for the admin
python manage.py runserver
```

That gives you the API at http://127.0.0.1:8000/api/tickers/ and the admin at
http://127.0.0.1:8000/admin/.

Frontend (in a second terminal):

```bash
cd frontend
npm install
cp .env.example .env              # points at the local backend by default
npm run dev
```

The dashboard is then at http://localhost:5173/. The database is just SQLite,
so there's nothing extra to set up. Running migrate creates the file.

## How the scraping works

Rather than parsing Yahoo's HTML, which is rendered with JavaScript and blocks
plain scrapers, I hit Yahoo's own JSON endpoints. These are the same ones the
website itself uses, so the data is clean and structured. There are three:

- the chart endpoint gives the current price and three months of daily history
- the quoteSummary endpoint gives the company profile and the detailed quote
  (this one needs a cookie and a "crumb" token, which the client fetches first)
- the search endpoint gives the recent news headlines

Every request has a timeout and retries a few times with a pause in between. The
delay, retry count and timeout are all read from environment variables. If a
field is missing I store null and carry on instead of letting the run crash. If
the crumb step fails I still save the price and history and mark the run as
Partial. Re-running a scrape doesn't create duplicates, because history has a
unique constraint on ticker plus date and news is unique on its URL. Every run
writes a log row recording whether it succeeded, partly succeeded, or failed.

You run the scraper like this:

```bash
python manage.py scrape AAPL          # one symbol
python manage.py scrape AAPL MSFT     # a few
python manage.py scrape --all         # everything in tickers.json
```

It isn't real-time. The dashboard shows whatever the last scrape saved, and
Yahoo's own numbers are delayed by around 15 minutes anyway.

## The API

Everything lives under `/api/` and the list endpoints are paginated (you can
pass `?page=` and `?page_size=`).

- `GET /tickers/` lists the tracked tickers, each with its latest quote
- `POST /tickers/` adds a ticker by symbol and scrapes it (body: `{"symbol": "NVDA"}`)
- `GET /tickers/{symbol}/` returns the full detail for one ticker
- `GET /tickers/{symbol}/history/` returns historical prices, and takes
  `?start=` and `?end=` to filter by date
- `GET /tickers/{symbol}/news/` returns the news articles for a ticker
- `GET /logs/` returns the recent scrape logs

A couple of example responses so you can see the shape.

`GET /api/tickers/AAPL/`

```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "exchange": "NasdaqGS",
  "currency": "USD",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "website": "https://www.apple.com",
  "business_summary": "Apple Inc. designs, manufactures, and markets ...",
  "full_time_employees": 164000,
  "last_scraped_at": "2026-09-09T10:15:00Z",
  "latest_quote": {
    "current_price": "234.0700",
    "change": "1.2300",
    "change_percent": "0.5280",
    "previous_close": "232.8400",
    "open_price": "233.1000",
    "days_low": "232.5000",
    "days_high": "235.2000",
    "week52_low": "164.0800",
    "week52_high": "260.1000",
    "volume": 41000000,
    "market_cap": 3600000000000,
    "pe_ratio": "35.6200",
    "eps": "6.5700",
    "scraped_at": "2026-09-09T10:15:00Z"
  }
}
```

`GET /api/tickers/AAPL/history/?page_size=3`

```json
{
  "count": 65,
  "next": "https://.../api/tickers/AAPL/history/?page=2&page_size=3",
  "previous": null,
  "results": [
    { "date": "2026-06-10", "open_price": "196.1000", "high_price": "198.2000",
      "low_price": "195.4000", "close_price": "197.8000", "volume": 52000000 }
  ]
}
```

`GET /api/tickers/AAPL/news/`

```json
{
  "count": 8,
  "results": [
    {
      "title": "Apple unveils new products at fall event",
      "url": "https://finance.yahoo.com/news/...",
      "source": "Reuters",
      "published_at": "2026-09-08T14:30:00Z",
      "published_raw": ""
    }
  ]
}
```

## Environment variables

The full list is in `backend/.env.example` and `frontend/.env.example`. On the
backend I use `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_PATH`,
`REQUEST_DELAY`, `RETRY_COUNT`, `REQUEST_TIMEOUT` and `USER_AGENT`. The frontend
only needs `VITE_API_BASE_URL`, which points it at the backend.

## Screenshots

<img width="887" height="1011" alt="1" src="https://github.com/user-attachments/assets/c06f9f8e-9e61-4e11-be08-9e160fdb038f" />
<img width="909" height="986" alt="2" src="https://github.com/user-attachments/assets/2a6d9141-596b-4c7c-ac62-fc452259c2d4" />
<img width="909" height="986" alt="3" src="https://github.com/user-attachments/assets/14eef84e-bd54-4d1a-8eaf-94837873bcd9" />

## A note on the deployment

The live database is seeded from a local scrape at build time, using
`seed_data.json`. I did it this way because Render's free tier wipes the
filesystem whenever the service restarts, and Yahoo tends to block requests
coming from cloud servers. The assignment allows this as long as it's mentioned,
so I'm mentioning it here. Tickers you add on the live site do work, but they
disappear on the next restart and the data goes back to the seeded set.

The backend build runs the migrations, loads `seed_data.json`, and collects
static files. It's served with gunicorn, and WhiteNoise handles the static
files for the admin.

## What I didn't do, and what I'd change with more time

The dashboard doesn't refresh on its own; the numbers are from the last scrape.
Anything added at runtime isn't permanent on the free tier, so for a real
version I'd move to Postgres with a persistent disk. Adding a ticker on the live
site scrapes live, which means it can fail if Yahoo blocks the server, though it
works fine locally. That add-ticker scrape also runs inside the request, so it's
a little slow; I'd push it to a background job. And to keep the data current I'd
add a scheduled scrape that runs on a timer.
