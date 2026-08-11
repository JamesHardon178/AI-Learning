export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"

export function getToken() {
  return localStorage.getItem("token")
}

export function setToken(token) {
  localStorage.setItem("token", token)
}

export function clearToken() {
  localStorage.removeItem("token")
}
