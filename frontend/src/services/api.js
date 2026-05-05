import axios from 'axios';

const api = axios.create({
  // Usa localhost para que coincida con http://localhost:5173
  // y el navegador pueda manejar correctamente la cookie de sesión.
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
