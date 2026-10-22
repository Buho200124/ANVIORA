/* ============================================================
   ANVIORA — Lógica de la pantalla de Login / Registro (RF-01)
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
  if (obtenerToken()) {
    location.href = "registro-diario.html";
    return;
  }

  const formLogin = document.getElementById("form-login");
  const formRegistro = document.getElementById("form-registro");
  const panelLogin = document.getElementById("panel-login");
  const panelRegistro = document.getElementById("panel-registro");

  document.getElementById("mostrar-registro").addEventListener("click", (evento) => {
    evento.preventDefault();
    panelLogin.classList.add("oculto");
    panelRegistro.classList.remove("oculto");
  });

  document.getElementById("mostrar-login").addEventListener("click", (evento) => {
    evento.preventDefault();
    panelRegistro.classList.add("oculto");
    panelLogin.classList.remove("oculto");
  });

  formLogin.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    ocultarMensaje("error-login");

    const correo = document.getElementById("login-correo").value.trim();
    const contrasena = document.getElementById("login-contrasena").value;

    establecerCargando("boton-login", true, "Iniciando sesión…");
    try {
      const datos = await llamarAPI("/api/auth/login", {
        metodo: "POST",
        cuerpo: { correo, contrasena },
        autenticado: false,
      });
      guardarToken(datos.access_token);
      location.href = "registro-diario.html";
    } catch (error) {
      mostrarMensaje("error-login", error.message);
    } finally {
      establecerCargando("boton-login", false);
    }
  });

  formRegistro.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    ocultarMensaje("error-registro");

    const nombre = document.getElementById("registro-nombre").value.trim();
    const correo = document.getElementById("registro-correo").value.trim();
    const contrasena = document.getElementById("registro-contrasena").value;

    if (contrasena.length < 8) {
      mostrarMensaje("error-registro", "La contraseña debe tener al menos 8 caracteres.");
      return;
    }

    establecerCargando("boton-registro", true, "Creando cuenta…");
    try {
      await llamarAPI("/api/auth/register", {
        metodo: "POST",
        cuerpo: { nombre, correo, contrasena },
        autenticado: false,
      });
      const datosLogin = await llamarAPI("/api/auth/login", {
        metodo: "POST",
        cuerpo: { correo, contrasena },
        autenticado: false,
      });
      guardarToken(datosLogin.access_token);
      location.href = "registro-diario.html";
    } catch (error) {
      mostrarMensaje("error-registro", error.message);
    } finally {
      establecerCargando("boton-registro", false);
    }
  });
});

function mostrarMensaje(id, texto) {
  const elemento = document.getElementById(id);
  elemento.textContent = texto;
  elemento.classList.remove("oculto");
}

function ocultarMensaje(id) {
  const elemento = document.getElementById(id);
  elemento.classList.add("oculto");
  elemento.textContent = "";
}

function establecerCargando(idBoton, cargando, textoCargando = "Cargando…") {
  const boton = document.getElementById(idBoton);
  if (cargando) {
    boton.dataset.textoOriginal = boton.textContent;
    boton.textContent = textoCargando;
    boton.disabled = true;
  } else {
    boton.textContent = boton.dataset.textoOriginal || boton.textContent;
    boton.disabled = false;
  }
}
