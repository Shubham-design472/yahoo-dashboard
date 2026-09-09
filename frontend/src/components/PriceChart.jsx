// Price chart built from the scraped historical data, with range options
// (the assignment asks for at least two). We have ~3 months of data, so 1M
// and 3M are the sensible ranges.

import { useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import { formatDate } from "../utils/format";

const RANGES = [
  { key: "1M", days: 30 },
  { key: "3M", days: 90 },
];

export default function PriceChart({ data }) {
  const [range, setRange] = useState("3M");

  const points = useMemo(() => {
    if (!data || data.length === 0) return [];
    const days = RANGES.find((r) => r.key === range)?.days ?? 90;
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);
    return data
      .filter((d) => new Date(d.date) >= cutoff)
      .map((d) => ({ date: d.date, close: Number(d.close_price) }));
  }, [data, range]);

  if (!data || data.length === 0) {
    return <div className="state state--empty">No price history to chart.</div>;
  }

  return (
    <div>
      <div className="range-buttons">
        {RANGES.map((r) => (
          <button
            key={r.key}
            type="button"
            className={`range-btn ${range === r.key ? "active" : ""}`}
            onClick={() => setRange(r.key)}
          >
            {r.key}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={points} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="date" tickFormatter={formatDate} minTickGap={44} />
          <YAxis domain={["auto", "auto"]} width={56} tickFormatter={(v) => v.toFixed(0)} />
          <Tooltip
            labelFormatter={formatDate}
            formatter={(v) => [Number(v).toFixed(2), "Close"]}
          />
          <Line type="monotone" dataKey="close" stroke="#2563eb" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
