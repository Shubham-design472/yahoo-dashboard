import { Routes, Route, Navigate } from "react-router-dom";
import TickerListPage from "./pages/TickerListPage";
import TickerDetailPage from "./pages/TickerDetailPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<TickerListPage />} />
      <Route path="/tickers/:symbol" element={<TickerDetailPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
