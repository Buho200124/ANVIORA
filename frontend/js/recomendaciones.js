/* ============================================================
   ANVIORA — Lista de recomendaciones de autocuidado (RF-04)
   ============================================================ */

async function cargarRecomendaciones() {
  const lista = document.getElementById("lista-recomendaciones");
  const vacio = document.getElementById("recomendaciones-vacio");

  try {
    const recomendaciones = await llamarAPI("/api/recommendations");
    lista.innerHTML = "";

    if (recomendaciones.length === 0) {
      vacio.classList.remove("oculto");
      lista.classList.add("oculto");
      return;
    }

    vacio.classList.add("oculto");
    lista.classList.remove("oculto");

    recomendaciones.forEach((recomendacion) => {
      lista.appendChild(crearElementoRecomendacion(recomendacion));
    });
  } catch (error) {
    vacio.textContent = error.message;
    vacio.classList.remove("oculto");
    lista.classList.add("oculto");
  }
}

function crearElementoRecomendacion(recomendacion) {
  const item = document.createElement("li");
  item.className = `recomendacion recomendacion--${recomendacion.nivel_prioridad}`;

  const contenido = document.createElement("div");
  contenido.className = "recomendacion__contenido";

  const etiqueta = document.createElement("span");
  etiqueta.className = "recomendacion__etiqueta";
  etiqueta.textContent = formatearTipoRecomendacion(recomendacion.tipo_recomendacion);

  const texto = document.createElement("p");
  texto.textContent = recomendacion.contenido_recomendacion;

  contenido.append(etiqueta, texto);
  item.appendChild(contenido);

  if (!recomendacion.vista) {
    const boton = document.createElement("button");
    boton.className = "boton-secundario";
    boton.type = "button";
    boton.textContent = "Marcar como vista";
    boton.addEventListener("click", async () => {
      boton.disabled = true;
      try {
        await llamarAPI(`/api/recommendations/${recomendacion.id_recomendacion}/marcar-vista`, { metodo: "PATCH" });
        cargarRecomendaciones();
      } catch (error) {
        boton.disabled = false;
        alert(error.message);
      }
    });
    item.appendChild(boton);
  }

  return item;
}

function formatearTipoRecomendacion(tipo) {
  const nombres = {
    autocuidado: "Autocuidado",
    estado_de_animo: "Estado de ánimo",
  };
  return nombres[tipo] || tipo;
}
