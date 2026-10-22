-- ============================================================================
-- ANVIORA · Datos de demostración: una semana de registros para UNA cuenta
-- ----------------------------------------------------------------------------
-- Siembra los 6 días anteriores a hoy (de hace 6 días a ayer) con una historia
-- coherente: semana de parciales que empieza tranquila y termina con estrés alto
-- y poco sueño. HOY queda libre para guardar el registro en vivo (así la
-- aplicación genera una alerta nueva durante la demostración).
--
-- Los análisis de IA y las recomendaciones sembradas son las mismas que el
-- sistema generaría con sus reglas para estos datos.
--
-- ⚠ Úsalo con una cuenta de DEMOSTRACIÓN: reemplaza los registros y las
--   recomendaciones de esos 6 días para ese correo. Se puede ejecutar varias veces.
--
-- Uso (desde la carpeta del proyecto; ver docs/OPERACION.md, sección 10):
--   docker compose cp ops/demo/demo_semana.sql db:/tmp/demo_semana.sql
--   docker compose exec db psql -U anviora_user -d anviora_db -v correo=demo@correo.com -f /tmp/demo_semana.sql
-- ============================================================================
\set ON_ERROR_STOP on

-- Siempre devuelve una fila (uid = 0 si la cuenta no existe) para poder avisar con un mensaje claro
SELECT COALESCE(MAX(id_usuario), 0) AS uid FROM usuarios WHERE correo = :'correo' \gset
SELECT (:uid > 0) AS existe \gset

\if :existe
BEGIN;

-- Limpia esa ventana de días para poder repetir el script sin duplicar datos
DELETE FROM recomendaciones
 WHERE id_usuario = :uid AND fecha_generacion::date BETWEEN CURRENT_DATE - 6 AND CURRENT_DATE - 1;
DELETE FROM registros_emocionales
 WHERE id_usuario = :uid AND fecha_registro BETWEEN CURRENT_DATE - 6 AND CURRENT_DATE - 1;

-- 1) Registros diarios (RF-02)
INSERT INTO registros_emocionales
    (id_usuario, fecha_registro, estado_animo, horas_sueno, nivel_estres, etiquetas_actividades, descripcion_texto, fecha_creacion)
VALUES
 (:uid, CURRENT_DATE - 6, 4, 7.50, 2, '{ejercicio,proyecto}',
  'Buen día, hice ejercicio y avancé en el proyecto.',                          (CURRENT_DATE - 6) + TIME '20:10'),
 (:uid, CURRENT_DATE - 5, 4, 7.00, 2, '{amigos,caminata}',
  'Día tranquilo, salí a caminar con mis amigos y me sentí relajado.',          (CURRENT_DATE - 5) + TIME '20:05'),
 (:uid, CURRENT_DATE - 4, 3, 6.50, 3, '{estudio}',
  'Empezó la semana de parciales, algo de presión pero manejable.',             (CURRENT_DATE - 4) + TIME '21:00'),
 (:uid, CURRENT_DATE - 3, 2, 5.00, 4, '{estudio,trabajo}',
  'Me quedé estudiando hasta tarde y dormí poco, me siento cansado.',           (CURRENT_DATE - 3) + TIME '22:15'),
 (:uid, CURRENT_DATE - 2, 2, 4.50, 5, '{estudio}',
  'Muy estresado por el examen de mañana, casi no pude dormir.',                (CURRENT_DATE - 2) + TIME '22:40'),
 (:uid, CURRENT_DATE - 1, 1, 4.00, 5, '{estudio}',
  'Me siento agotado y sin energía, el examen salió peor de lo esperado.',      (CURRENT_DATE - 1) + TIME '21:30');

-- 2) Análisis de IA de cada registro (RF-03)
INSERT INTO analisis_ia
    (id_registro, polaridad_sentimiento, puntuacion_confianza, palabras_clave, estado_procesamiento, fecha_procesamiento, fecha_creacion)
SELECT r.id_registro, a.pol, a.conf, a.claves, 'completado', r.fecha_creacion + INTERVAL '4 seconds', r.fecha_creacion
  FROM registros_emocionales r
  JOIN (VALUES
        (6, 'Positivo', 0.9412, ARRAY['ejercicio','avancé','proyecto']),
        (5, 'Positivo', 0.9021, ARRAY['caminar','amigos','relajado']),
        (4, 'Neutro',   0.6130, ARRAY['parciales','semana','presión','manejable']),
        (3, 'Negativo', 0.9215, ARRAY['estudiando','tarde','dormí','cansado']),
        (2, 'Negativo', 0.9650, ARRAY['estresado','examen','dormir']),
        (1, 'Negativo', 0.9803, ARRAY['agotado','energía','examen','peor'])
       ) AS a(dias, pol, conf, claves)
    ON r.fecha_registro = CURRENT_DATE - a.dias
 WHERE r.id_usuario = :uid;

-- 3) Recomendaciones (RF-04): las que el motor de reglas generaría con estos datos
--    · hace 6 días: estrés bajo y buen sueño  -> mensaje positivo (ya vista)
--    · ayer: 3 días seguidos con estrés >= 4 y < 6 h de sueño, y 3 análisis negativos -> 2 alertas altas (sin ver)
INSERT INTO recomendaciones
    (id_usuario, id_registro, tipo_recomendacion, contenido_recomendacion, nivel_prioridad, vista, fecha_generacion)
SELECT :uid, r.id_registro, v.tipo, v.contenido, v.prioridad, v.vista, r.fecha_creacion + INTERVAL '5 seconds'
  FROM (VALUES
        (6, 'autocuidado',
            '¡Vas muy bien! Mantén tu rutina de sueño y sigue registrando cómo te sientes.', 'baja', true),
        (1, 'autocuidado',
            'Llevas varios días con estrés alto y poco descanso. Considera priorizar el sueño esta noche y tomar pausas activas durante el día.', 'alta', false),
        (1, 'estado_de_animo',
            'Tu descripción del día ha reflejado un tono negativo varias veces seguidas. Hablar con alguien de confianza o un profesional puede ayudarte.', 'alta', false)
       ) AS v(dias, tipo, contenido, prioridad, vista)
  JOIN registros_emocionales r ON r.id_usuario = :uid AND r.fecha_registro = CURRENT_DATE - v.dias;

COMMIT;

\echo
\echo '✔ Datos de demostración cargados para' :correo
SELECT r.fecha_registro AS fecha, r.estado_animo AS animo, r.horas_sueno AS sueno, r.nivel_estres AS estres,
       a.polaridad_sentimiento AS sentimiento
  FROM registros_emocionales r LEFT JOIN analisis_ia a USING (id_registro)
 WHERE r.id_usuario = :uid AND r.fecha_registro >= CURRENT_DATE - 6
 ORDER BY r.fecha_registro;
\echo 'Ahora guarda el registro de HOY desde la aplicación (estrés 4-5 y menos de 6 h de sueño) para ver una alerta nueva.'

\else
\echo
\echo 'ERROR: no existe ningún usuario con el correo' :correo
\echo 'Primero crea esa cuenta en http://localhost:8000 y vuelve a ejecutar el script.'
\endif
