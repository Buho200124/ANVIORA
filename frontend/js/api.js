/* ============================================================
   ANVIORA — Cliente HTTP hacia el backend (API REST)
   Centraliza la URL base, el token JWT y el manejo de errores
   para que las demás páginas solo llamen a llamarAPI().
   ============================================================ */

// Si el frontend lo sirve el gateway (http://localhost:8000), la API está en el mismo origen.
// Si se abre como archivo o con un servidor estático aparte (ej. puerto 5500), apunta al gateway.
const API_BASE_URL =
  location.protocol === "file:" || location.port === "5500" ? "http://localhost:8000" : "";
const CLAVE_TOKEN = "anviora_token";

function obtenerToken() {
  return localStorage.getItem(CLAVE_TOKEN);
}

function guardarToken(token) {
  localStorage.setItem(CLAVE_TOKEN, token);
}

function eliminarToken() {
  localStorage.removeItem(CLAVE_TOKEN);
}

/**
 * Llama a un endpoint de la API de ANVIORA.
 * @param {string} ruta - Ruta relativa, ej. "/api/logs".
 * @param {object} opciones
 * @param {"GET"|"POST"|"PATCH"|"DELETE"} [opciones.metodo]
 * @param {object|null} [opciones.cuerpo]
 * @param {boolean} [opciones.autenticado] - Si debe enviar el JWT.
 */
async function llamarAPI(ruta, { metodo = "GET", cuerpo = null, autenticado = true } = {}) {
  const cabeceras = { "Content-Type": "application/json" };

  if (autenticado) {
    const token = obtenerToken();
    if (token) {
      cabeceras.Authorization = `Bearer ${token}`;
    }
  }

  const opcionesFetch = { method: metodo, headers: cabeceras };
  if (cuerpo !== null) {
    opcionesFetch.body = JSON.stringify(cuerpo);
  }

  let respuesta;
  try {
    respuesta = await fetch(`${API_BASE_URL}${ruta}`, opcionesFetch);
  } catch (errorRed) {
    throw new Error("No se pudo conectar con el servidor. Verifica que el backend esté corriendo.");
  }

  const datos = await respuesta.json().catch(() => ({}));

  if (!respuesta.ok) {
    if (respuesta.status === 401 && autenticado) {
      eliminarToken();
      if (!location.pathname.endsWith("index.html") && location.pathname !== "/") {
        location.href = "index.html";
      }
    }
    const mensaje = datos.mensaje || datos.detail || "Ocurrió un error inesperado.";
    throw new Error(mensaje);
  }

  return datos;
}

/** Redirige al login si no hay sesión activa. Se llama al cargar páginas privadas. */
function protegerPagina() {
  if (!obtenerToken()) {
    location.href = "index.html";
  }
}
