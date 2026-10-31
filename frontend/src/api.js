import axios from "axios";

const API_URL = "http://localhost:8000/api";

const api = axios.create({ baseURL: API_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const refresh = localStorage.getItem("refresh");
    const canRetry =
      error.response?.status === 401 &&
      refresh &&
      !original._retry &&
      !original.url.includes("/auth/login/");

    if (canRetry) {
      original._retry = true;
      try {
        const { data } = await axios.post(`${API_URL}/auth/token/refresh/`, { refresh });
        localStorage.setItem("access", data.access);
        original.headers.Authorization = `Bearer ${data.access}`;
        return api(original);
      } catch {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
      }
    }
    return Promise.reject(error);
  }
);

export function errorMessage(error) {
  const data = error.response?.data;
  if (!data) return "No se pudo conectar con el servidor.";
  if (typeof data === "string") return "Error del servidor.";
  if (data.detail) return data.detail;
  return Object.entries(data)
    .map(([field, msgs]) => `${field}: ${[].concat(msgs).join(" ")}`)
    .join(" | ");
}

export default api;