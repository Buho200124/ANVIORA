/* ============================================================
   ANVIORA — Lógica del Formulario Diario de Estado Emocional (RF-02)
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
  protegerPagina();

  const fechaEl = document.getElementById("fecha-hoy");
  if (fechaEl) {
    fechaEl.textContent = new Intl.DateTimeFormat("es-CO", {
      weekday: "long",
      day: "numeric",
      month: "long",
    }).format(new Date());
  }

  const inputHorasSueno = document.getElementById("horas-sueno");
  const valorHorasSueno = document.getElementById("valor-horas-sueno");
  const actualizarValorSueno = () => {
    valorHorasSueno.textContent = `${inputHorasSueno.value} h`;
  };
  inputHorasSueno.addEventListener("input", actualizarValorSueno);
  actualizarValorSueno();

  const textareaDescripcion = document.getElementById("descripcion-texto");
  const contador = document.getElementById("contador-caracteres");
  textareaDescripcion.addEventListener("input", () => {
    contador.textContent = `${textareaDescripcion.value.length} / 2000`;
  });

  const formulario = document.getElementById("form-registro-diario");
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    ocultarMensajesFormulario();

    const estadoAnimo = Number(formulario.querySelector('input[name="estado-animo"]:checked')?.value || 0);
    const nivelEstres = Number(formulario.querySelector('input[name="nivel-estres"]:checked')?.value || 0);

    if (!estadoAnimo || !nivelEstres) {
      mostrarMensajeFormulario("error", "Selecciona tu estado de ánimo y tu nivel de estrés antes de guardar.");
      return;
    }

    const etiquetas = Array.from(formulario.querySelectorAll('input[name="etiquetas"]:checked')).map((el) => el.value);
    const otraEtiqueta = document.getElementById("otra-etiqueta").value.trim();
    if (otraEtiqueta) {
      etiquetas.push(otraEtiqueta.toLowerCase());
    }

    const cuerpo = {
      estado_animo: estadoAnimo,
      horas_sueno: Number(inputHorasSueno.value),
      nivel_estres: nivelEstres,
      etiquetas_actividades: etiquetas,
      descripcion_texto: textareaDescripcion.value.trim() || null,
    };

    const boton = document.getElementById("boton-guardar");
    boton.disabled = true;
    boton.textContent = "Guardando…";

    try {
      await llamarAPI("/api/logs", { metodo: "POST", cuerpo });
      mostrarMensajeFormulario(
        "exito",
        "Registro guardado. Tu análisis se está procesando; en un momento verás resultados en el dashboard."
      );
      formulario.reset();
      actualizarValorSueno();
      contador.textContent = "0 / 2000";
      setTimeout(() => {
        location.href = "dashboard.html";
      }, 1600);
    } catch (error) {
      mostrarMensajeFormulario("error", error.message);
    } finally {
      boton.disabled = false;
      boton.textContent = "Guardar registro";
    }
  });
});

function mostrarMensajeFormulario(tipo, texto) {
  const elemento = document.getElementById(`mensaje-${tipo}`);
  elemento.textContent = texto;
  elemento.classList.remove("oculto");
}

function ocultarMensajesFormulario() {
  ["error", "exito"].forEach((tipo) => {
    const elemento = document.getElementById(`mensaje-${tipo}`);
    elemento.classList.add("oculto");
    elemento.textContent = "";
  });
}
