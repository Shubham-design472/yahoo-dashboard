import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getTickers, addTicker } from "../api";
import { Loading, EmptyState, ErrorView } from "../components/StateViews";
import {
  formatPrice,
  formatChange,
  formatPercent,
  formatCompact,
  changeClass,
} from "../utils/format";

function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

const COLUMNS = [
  { key: "symbol", label: "Symbol" },
  { key: "company_name", label: "Company" },
  { key: "price", label: "Price" },
  { key: "change", label: "Change" },
  { key: "change_percent", label: "% Change" },
  { key: "market_cap", label: "Market Cap" },
];

export default function TickerListPage() {
  const [tickers, setTickers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);

  const [sortKey, setSortKey] = useState("symbol");
  const [sortDir, setSortDir] = useState("asc");

  const [addSymbol, setAddSymbol] = useState("");
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState("");

  const loadTickers = async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await getTickers({ page_size: 500 });
      setTickers(data.results ?? []);
    } catch (err) {
      console.error("Failed to fetch tickers:", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickers();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    const symbol = addSymbol.trim().toUpperCase();
    if (!symbol) return;

    setAdding(true);
    setAddError("");

    try {
      await addTicker(symbol);
      setAddSymbol("");
      await loadTickers();
    } catch (err) {
      console.error("Error adding ticker:", err);
      const detail = err?.response?.data?.detail;
      setAddError(
        detail || "Could not add that symbol. Please check it and try again."
      );
    } finally {
      setAdding(false);
    }
  };

  const getSortValue = (item, key) => {
    const quote = item.latest_quote || {};
    switch (key) {
      case "symbol":
        return item.symbol || "";
      case "company_name":
        return item.company_name || "";
      case "price":
        return Number(quote.current_price) || 0;
      case "change":
        return Number(quote.change) || 0;
      case "change_percent":
        return Number(quote.change_percent) || 0;
      case "market_cap":
        return Number(quote.market_cap) || 0;
      default:
        return "";
    }
  };

  const visibleTickers = useMemo(() => {
    const query = debouncedSearch.trim().toLowerCase();

    const filtered = tickers.filter((item) => {
      if (!query) return true;
      const symbolMatches = item.symbol?.toLowerCase().includes(query);
      const companyMatches = item.company_name?.toLowerCase().includes(query);
      return symbolMatches || companyMatches;
    });

    return [...filtered].sort((a, b) => {
      const valA = getSortValue(a, sortKey);
      const valB = getSortValue(b, sortKey);

      let comparison = 0;
      if (typeof valA === "number" && typeof valB === "number") {
        comparison = valA - valB;
      } else {
        comparison = String(valA).localeCompare(String(valB));
      }

      return sortDir === "asc" ? comparison : -comparison;
    });
  }, [tickers, debouncedSearch, sortKey, sortDir]);

  const handleSort = (key) => {
    if (key === sortKey) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Stock Dashboard</h1>

      <div className="toolbar">
        <input
          className="input"
          placeholder="Search by symbol or company..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <form className="add-form" onSubmit={handleAdd}>
          <input
            className="input"
            placeholder="Add symbol (e.g. NVDA)"
            value={addSymbol}
            onChange={(e) => setAddSymbol(e.target.value)}
          />
          <button className="btn" type="submit" disabled={adding}>
            {adding ? "Adding..." : "Add"}
          </button>
        </form>
      </div>

      {addError && <div className="inline-error">{addError}</div>}

      {loading ? (
        <Loading label="Loading tickers..." />
      ) : error ? (
        <ErrorView label="Couldn't load tickers. Is the backend running?" />
      ) : visibleTickers.length === 0 ? (
        <EmptyState label="No tickers to show. Add one above to get started." />
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                {COLUMNS.map((col) => (
                  <th
                    key={col.key}
                    className="sortable"
                    onClick={() => handleSort(col.key)}
                  >
                    {col.label}
                    {sortKey === col.key && (sortDir === "asc" ? " ▲" : " ▼")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visibleTickers.map((ticker) => {
                const quote = ticker.latest_quote || {};
                return (
                  <tr key={ticker.symbol}>
                    <td>
                      <Link className="link" to={`/tickers/${ticker.symbol}`}>
                        {ticker.symbol}
                      </Link>
                    </td>
                    <td>{ticker.company_name || "—"}</td>
                    <td>{formatPrice(quote.current_price)}</td>
                    <td className={changeClass(quote.change)}>
                      {formatChange(quote.change)}
                    </td>
                    <td className={changeClass(quote.change_percent)}>
                      {formatPercent(quote.change_percent)}
                    </td>
                    <td>{formatCompact(quote.market_cap)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
