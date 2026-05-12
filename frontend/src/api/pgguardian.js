/*
Este es el Cliente API para PgGuardian.

Aquí se va a centralizar todas las llamadas al backend de FastAPI.
Se usa un Base URL configurable, manejo de errores y función fullScan 
que ejecuta todos los detectores en una sola petición.
*/

const API_BASE = 'http://localhost:8000/api';

async function fetchJSON(endpoint) {
  const res = await fetch(`${API_BASE}${endpoint}`);
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}


// En esta parte van a estar todas llas funciones que estén en el API del Backend
// Cuando estén las apis listas, se van a agregar sus exports aquí