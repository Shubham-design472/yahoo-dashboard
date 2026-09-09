const FALLBACK = "—";

function toNum(val) {
  if (val === null || val === undefined || val === "") return null;
  const n = Number(val);
  return Number.isNaN(n) ? null : n;
}

export function formatCompact(value) {
  const n = toNum(value);
  if (n === null) return FALLBACK;

  const abs = Math.abs(n);
  if (abs >= 1e12) return `${(n / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(n / 1e6).toFixed(2)}M`;

  return n.toLocaleString("en-US");
}

export function formatInteger(value) {
  const n = toNum(value);
  if (n === null) return FALLBACK;
  return Math.round(n).toLocaleString("en-US");
}

export function formatPrice(value) {
  const n = toNum(value);
  if (n === null) return FALLBACK;

  return n.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function formatChange(value) {
  const n = toNum(value);
  if (n === null) return FALLBACK;
  return `${n > 0 ? "+" : ""}${n.toFixed(2)}`;
}

export function formatPercent(value) {
  const n = toNum(value);
  if (n === null) return FALLBACK;
  return `${n > 0 ? "+" : ""}${n.toFixed(2)}%`;
}

export function formatDate(value) {
  if (value === null || value === undefined || value === "") return FALLBACK;

  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);

  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function changeClass(value) {
  const n = Number(value);
  if (!n || Number.isNaN(n)) return "flat";
  return n > 0 ? "up" : "down";
}
