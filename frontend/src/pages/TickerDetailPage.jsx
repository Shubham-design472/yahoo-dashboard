import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getTicker, getHistory, getNews } from "../api";
import { Loading, EmptyState, ErrorView } from "../components/StateViews";
import PriceChart from "../components/PriceChart";
import {
  formatPrice,
  formatChange,
  formatPercent,
  formatCompact,
  formatInteger,
  formatDate,
  changeClass,
} from "../utils/format";

function BackLink() {
  return (
    <Link className="link back" to="/">
      ← Back to all tickers
    </Link>
  );
}

export default function TickerDetailPage() {
  const { symbol } = useParams();

  const [ticker, setTicker] = useState(null);
  const [history, setHistory] = useState([]);
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function loadTickerData() {
      setLoading(true);
      setError(false);

      try {
        const [tickerRes, historyRes, newsRes] = await Promise.all([
          getTicker(symbol),
          getHistory(symbol, { page_size: 500 }),
          getNews(symbol, { page_size: 20 }),
        ]);

        if (!isMounted) return;

        setTicker(tickerRes);
        setHistory(historyRes?.results ?? []);
        setNews(newsRes?.results ?? []);
      } catch (err) {
        console.error("Error fetching ticker details:", err);
        if (isMounted) setError(true);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadTickerData();

    return () => {
      isMounted = false;
    };
  }, [symbol]);

  if (loading) {
    return (
      <div className="page">
        <Loading label={`Loading ${symbol}...`} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <BackLink />
        <ErrorView label="Couldn't load this ticker. Please try again." />
      </div>
    );
  }

  if (!ticker) {
    return (
      <div className="page">
        <BackLink />
        <EmptyState label="Ticker not found." />
      </div>
    );
  }

  const quote = ticker.latest_quote || {};

  const quoteMetrics = [
    ["Previous Close", formatPrice(quote.previous_close)],
    ["Open", formatPrice(quote.open_price)],
    ["Day's Low", formatPrice(quote.days_low)],
    ["Day's High", formatPrice(quote.days_high)],
    ["52-Week Low", formatPrice(quote.week52_low)],
    ["52-Week High", formatPrice(quote.week52_high)],
    ["Volume", formatInteger(quote.volume)],
    ["Market Cap", formatCompact(quote.market_cap)],
    ["P/E (TTM)", quote.pe_ratio ? Number(quote.pe_ratio).toFixed(2) : "—"],
    ["EPS (TTM)", quote.eps ? Number(quote.eps).toFixed(2) : "—"],
  ];

  return (
    <div className="page">
      <BackLink />

      <div className="detail-header">
        <div>
          <h1 className="page-title">
            {ticker.symbol}
            <span className="muted"> · {ticker.exchange || "—"}</span>
          </h1>
          <div className="company-name">{ticker.company_name || "—"}</div>
        </div>

        <div className="price-block">
          <div className="big-price">
            {formatPrice(quote.current_price)}{" "}
            <span className="muted">{ticker.currency || ""}</span>
          </div>
          <div className={`change ${changeClass(quote.change)}`}>
            {formatChange(quote.change)} ({formatPercent(quote.change_percent)})
          </div>
        </div>
      </div>

      <div className="grid">
        <section className="card">
          <h2 className="card-title">Price history</h2>
          <PriceChart data={history} />
        </section>

        <section className="card">
          <h2 className="card-title">Quote</h2>
          <table className="kv-table">
            <tbody>
              {quoteMetrics.map(([label, value]) => (
                <tr key={label}>
                  <th>{label}</th>
                  <td>{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>

      <section className="card">
        <h2 className="card-title">
          About {ticker.company_name || ticker.symbol}
        </h2>
        <div className="company-meta">
          <span>
            <strong>Sector:</strong> {ticker.sector || "—"}
          </span>
          <span>
            <strong>Industry:</strong> {ticker.industry || "—"}
          </span>
          <span>
            <strong>Employees:</strong> {formatInteger(ticker.full_time_employees)}
          </span>
          {ticker.website && (
            <span>
              <strong>Website:</strong>{" "}
              <a 
                className="link" 
                href={ticker.website} 
                target="_blank" 
                rel="noreferrer"
              >
                {ticker.website}
              </a>
            </span>
          )}
        </div>
        <p className="summary">
          {ticker.business_summary || "No description available."}
        </p>
      </section>

      <section className="card">
        <h2 className="card-title">Recent news</h2>
        {news.length === 0 ? (
          <EmptyState label="No news articles found." />
        ) : (
          <ul className="news-list">
            {news.map((item) => (
              <li key={item.url} className="news-item">
                <a
                  className="news-title"
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {item.title}
                </a>
                <div className="news-meta">
                  {item.source || "Unknown"} ·{" "}
                  {item.published_at ? formatDate(item.published_at) : item.published_raw || ""}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
