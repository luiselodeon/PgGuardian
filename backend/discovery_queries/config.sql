/*
PgGuardian — Detección de Configuración

En esta sección se documentan los queries con los cuales se encontraron 
desviaciones en los parámetros de pg_settings, comparando la configuración 
actual de memoria (shared_buffers, work_mem) y niveles de log 
contra los valores óptimos para el volumen de datos de la instancia.
*/

/*
Asegurar correcto alcance de pg_stat_statements
Si el límite de consultas (max) es muy pequeño, el sistema de estadísticas
se satura y se pierde el historial de rendimiento acumulado.
*/
SELECT
    'pg_stat_statements.max' AS parameter,
 -- Valor actual configurado en el servidor
    s.setting AS configured_value,

    /* Validación de Dependencia:
       Verifica si la extensión existe en la base de datos actual.
    */
    -- Verificar que la extensión esté cargada (si no, reportar otra cosa)
    EXISTS( SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements') AS extension_loaded,

    'pg_stat_statements.max controla cuántas queries únicas son trackeadas. '
    || 'Valores < 1000 causan eviction frecuente y pérdida de visibilidad '
    || 'sobre el workload real de la base de datos.' AS description,

    -- Acción correctiva específica
    'Subir a 5000-10000. Cambio requiere reinicio del servidor.' AS recommendation,

    -- Bloque de código listo para copiar y pegar en postgresql.conf
    '-- En postgresql.conf:' || chr(10)
    || 'pg_stat_statements.max = 5000' || chr(10)
    || '-- Reiniciar PostgreSQL después del cambio' AS suggested_action,

    'pg_stat_statements.max muy bajo (tracking insuficiente)' AS finding_id,

    /*
    - < 500: MEDIUM (Casi garantizado que se pierden datos en producción)
    - 500 a 1000: LOW (Riesgo bajo pero presente)
    */
    CASE
        WHEN s.setting::int < 500 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS severity

FROM pg_settings s

-- Buscamos el parámetro específico en el catálogo de ajustes del motor
WHERE s.name = 'pg_stat_statements.max'
/* Umbral de activación.
       1000 es el valor por defecto de postgres. Para aplicaciones modernas
       con ORMs que generan muchas queries, esto suele ser insuficiente
    */
  AND s.setting::int < 1000
  -- Solo reportar si la extensión efectivamente está cargada
  AND EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements');

/*
Referencias:
-PostgreSQL. (2026). F.32. pg_stat_statements — Configuration Parameters. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/current/pgstatstatements.html
-PostgreSQL. (2026). 53.25. pg_settings. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/view-pg-settings.html
-PostgreSQL. (2026). 52.22. pg_extension. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/current/catalog-pg-extension.html
-PostgreSQL. (2026). 9.4. String Functions and Operators (chr). PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/functions-string.html
*/

/*
Problema: Configuración de los logs desactivado

Este query tiene como objetivo detectar si es que la configuración de los logs
está desactivada, esto se ve con un valor de -1. Esto se hace para que posteriormente
se pueda hacer la recomendación de activar la configuración de los logs y poner un valor
neutral para el negocio como 1000 ms.
*/

SELECT
    name, -- Nombre del parámetro
    setting AS current_value, -- Valor configurado actualmente
    unit, -- Unidad de medida
    short_desc
FROM
    pg_settings
WHERE
    name = 'log_min_duration_statement';

/*
Referencias:

-PostgreSQL. (2026). 53.25. pg_settings. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/current/view-pg-settings.html
*/