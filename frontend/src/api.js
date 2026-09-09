import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 40000,
});

export const getTickers = async (params = {}) => {
  const { data } = await api.get("/tickers/", { params });
  return data;
};

export const getTicker = async (symbol) => {
  const { data } = await api.get(`/tickers/${encodeURIComponent(symbol)}/`);
  return data;
};

export const addTicker = async (symbol) => {
  const { data } = await api.post("/tickers/", { symbol });
  return data;
};

export const getHistory = async (symbol, params = {}) => {
  const { data } = await api.get(`/tickers/${encodeURIComponent(symbol)}/history/`, { params });
  return data;
};

export const getNews = async (symbol, params = {}) => {
  const { data } = await api.get(`/tickers/${encodeURIComponent(symbol)}/news/`, { params });
  return data;
};

export const getLogs = async (params = {}) => {
  const { data } = await api.get("/logs/", { params });
  return data;
};

export default api;
