/* ============================================================
   ANVIORA — Lógica del Dashboard (RF-05)
   Gráfica de tendencias con Chart.js + filtro semanal/mensual.
   ============================================================ */

let grafico = null;

document.addEventListener("DOMContentLoaded", () => {
  protegerPagina();

  document.getElementById("boton-cerrar-sesion").addEventListener("click", cerrarSesion);

  document.querySelectorAll(".filtro-periodo").forEach((boton) => {
    boton.addEventListener("click", () => {
      document.querySelectorAll(".filtro-periodo").forEach((b) => b.classList.remove("activo"));
      boton.classList.add("activo");
      cargarEstadisticas(boton.dataset.periodo);
    });
  });

  cargarEstadisticas("semanal");
  cargarRecomendaciones();
});

async function cerrarSesion() {
  try {
    await llamarAPI("/api/auth/logout", { metodo: "POST" });
  } catch (error) {
    /* Aunque falle en el servidor, igual cerramos la sesión localmente. */
  } finally {
    eliminarToken();
    location.href = "index.html";
  }
}

async function cargarEstadisticas(periodo) {
  const sinDatos = document.getElementById("sin-datos");
  const contenedorGrafico = document.getElementById("contenedor-grafico");

  try {
    const datos = await llamarAPI(`/api/dashboard/stats?periodo=${periodo}`);

    if (datos.fechas.length === 0) {
      sinDatos.classList.remove("oculto");
      contenedorGrafico.classList.add("oculto");
      return;
    }

    sinDatos.classList.add("oculto");
    contenedorGrafico.classList.remove("oculto");
    renderizarGrafico(datos);
  } catch (error) {
    sinDatos.textContent = error.message;
    sinDatos.classList.remove("oculto");
    contenedorGrafico.classList.add("oculto");
  }
}

function renderizarGrafico(datos) {
  const lienzo = document.getElementById("grafico-tendencias");
  const configuracion = {
    type: "line",
    data: {
      labels: datos.fechas,
      datasets: [
        {
          label: "Estado de ánimo",
          data: datos.estado_animo,
          borderColor: "#3D5A80",
          backgroundColor: "rgba(61, 90, 128, 0.15)",
          tension: 0.3,
          yAxisID: "yEscala",
        },
        {
          label: "Nivel de estrés",
          data: datos.nivel_estres,
          borderColor: "#A24A50",
          backgroundColor: "rgba(162, 74, 80, 0.15)",
          tension: 0.3,
          yAxisID: "yEscala",
        },
        {
          label: "Horas de sueño",
          data: datos.horas_sueno,
          borderColor: "#C97A3F",
          backgroundColor: "rgba(201, 122, 63, 0.15)",
          tension: 0.3,
          yAxisID: "ySueno",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "bottom" },
      },
      scales: {
        yEscala: {
          type: "linear",
          position: "left",
          min: 0,
          max: 5,
          title: { display: true, text: "Ánimo / Estrés (1-5)" },
        },
        ySueno: {
          type: "linear",
          position: "right",
          min: 0,
          max: 14,
          grid: { drawOnChartArea: false },
          title: { display: true, text: "Horas de sueño" },
        },
      },
    },
  };

  if (grafico) {
    grafico.data = configuracion.data;
    grafico.options = configuracion.options;
    grafico.update();
  } else {
    grafico = new Chart(lienzo, configuracion);
  }
}
