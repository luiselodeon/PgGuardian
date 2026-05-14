/*
PgGuardian — Detección de Salud Operativa

En esta sección se documentan los queries con los cuales se encontraron 
riesgos para la estabilidad del motor, identificando conexiones en estado 
idle in transaction de larga duración y tablas de gran volumen que 
carecen de políticas de retención de datos.
*/

/*Para poder identificar los siguientes problemas:
tablas no particionadas
tablas con un crecimiento significativo
tablas con más de 500 MB
tablas que no tienen un política de retención
utilizamos la extensión pg_partman, esta extensión tiene el objetivo automatizar y gestionar particiones de tablas


Referencias:
9.28. System Administration Functions. (2026, 26 febrero). PostgreSQL Documentation. https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADMIN-DBOBJECT
27.2. The Cumulative Statistics System. (2026, 26 febrero). PostgreSQL Documentation. https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ALL-TABLES-VIEW
52.11. pg_class. (2026, 26 febrero). PostgreSQL Documentation. https://www.postgresql.org/docs/current/catalog-pg-class.html
Auto-archiving and Data Retention Management in Postgres with pg_partman | Crunchy Data Blog. (2024, 19 abril). Crunchy Data. https://www.crunchydata.com/blog/auto-archiving-and-data-retention-management-in-postgres-with-pg_partman
Pgpartman. (2026). GitHub - pgpartman/pg_partman: Partition management extension for PostgreSQL. GitHub. https://github.com/pgpartman/pg_partman
*/

/*Un SCHEMA organiza los objetos de una base de datos en grupos lógicos
se hace un SCHEMA porque pg_partman tiene todas las funciones y tablas necesarias para funcionar y podrían mezclarse
con la información de otras tablas

Referencias:
Fantasma del teclado. (2021, 26 abril). 🐘 Postgres || Qué es un schema || CREATE SCHEMA [Vídeo]. YouTube. https://www.youtube.com/watch?v=FfYpMjWivos*/

CREATE SCHEMA partman;

-- Instalamos la extensión dentro del SCHEMA
CREATE EXTENSION pg_partman SCHEMA partman;

/*Significado de columnas:
schemaname: nombre del schema
relname: nombre de la tabla
total_table_size: tamaño total de la tabla
size_mb: tamaño en MB
total_inserts_history: número de filas insertadas en esa tabla
total_deletes_history: número de filas eliminadas en esa tabla
delete_ratio_oct: procentaje de los datos insertados que han sido eliminados*/

SELECT
    stat.schemaname,
    stat.relname AS table_name,
    pg_size_pretty(pg_total_relation_size(stat.relid)) AS total_table_size,
    pg_total_relation_size(stat.relid) / (1024*1024) AS size_mb,
    stat.n_tup_ins AS total_inserts_history,
    stat.n_tup_del AS total_deletes_history,
    -- Porcentaje de registros insertados que han sido eliminados
    CASE
        WHEN stat.n_tup_ins > 0 THEN ROUND((stat.n_tup_del::numeric / stat.n_tup_ins) * 100, 2)
        ELSE 0
    END AS delete_ratio_pct
FROM pg_stat_user_tables stat
JOIN pg_class c ON stat.relid = c.oid
WHERE
    -- Tablas no particionadas
    c.relkind = 'r'
    OR c.relispartition = false

    -- Tablas con más de 100 000 inserts
    OR stat.n_tup_ins > 100000

    -- Tablas que pesen mas de 500 MB
    OR pg_total_relation_size(stat.relid) > 500 * 1024 * 1024

    -- Tablas sin politicas de retencion
    OR (
        stat.n_tup_ins = 0
        OR (stat.n_tup_del::numeric / stat.n_tup_ins) < 0.05
    )
ORDER BY pg_total_relation_size(stat.relid) DESC;

/* Detector de transacciones inactivas (Idle in Transaction)
   Identifica procesos que abrieron una transacción y no la han cerrado,
   lo cual previene que el motor limpie filas muertas (bloat) y mantiene
   locks activos innecesariamente.
*/
SELECT
    'pg_stat_activity' AS parameter,
    pid AS configured_value,

	-- Describe que PID está causando el bloqueo, su estado y cuánto tiempo lleva activo en minutos.
    'La conexión (PID ' || pid || ') está bloqueando recursos. '
    || 'Estado actual: ' || state
    || '. Tiempo activa/inactiva: '
    || ROUND(EXTRACT(EPOCH FROM (NOW() - state_change)) / 60, 2)
    || ' minutos.' AS description,

	-- Se recomienda terminar la conexión con ese PID.
    'Terminar la conexión con pg_terminate_backend(' || pid || ') '
    || 'o configurar idle_in_transaction_session_timeout.' AS recommendation,

    'Conexión de larga duración detectada' AS finding_id,

	-- Si el bloqueo lleva dos minutos activo, se determina como severidad alta.
	-- Si el bloqueo lleva un minuto activo, se clasifica como serveridad media.
    CASE
        WHEN state_change < NOW() - INTERVAL '2 minutes' THEN 'HIGH'
        WHEN state_change < NOW() - INTERVAL '1 minute' THEN 'MEDIUM'
    END AS severity

FROM pg_stat_activity
WHERE
	 -- Detecta transacciones olvidadas (IDLE) o consultas activas excesivamente largas.
    (state = 'idle in transaction' OR state = 'active')
    AND state_change < NOW() - INTERVAL '1 minute'
    AND pid <> pg_backend_pid()
	-- Filtro para sólo reportar si es el usuario de la tienda.
    AND usename = 'tienda_user';

/*
Referencias:
-Sruthi Ganesh. (2024). Managing Open Idle Connections in PostgreSQL. Medium. https://medium.com/@sruthiganesh/managing-open-idle-connections-in-postgresql-1b884a5f2c67
-System administration functions. (2018, 8 noviembre). PostgreSQL Documentation. https://www.postgresql.org/docs/9.3/functions-admin.html
-How to Find and Stop Running Queries on PostgreSQL - Adam Johnson. (2022, 20 junio). https://adamj.eu/tech/2022/06/20/how-to-find-and-stop-running-queries-on-postgresql/
-Stephan. (2013, 4 octubre). How to convert interval to timestamp with time zone with postgresql? Stack Overflow. https://stackoverflow.com/questions/19183916/how-to-convert-interval-to-timestamp-with-time-zone-with-postgresql
-Date/Time Functions and Operators. (2012, 1 enero). PostgreSQL Documentation. https://www.postgresql.org/docs/8.1/functions-datetime.html
-System Information functions. (2020, 13 febrero). PostgreSQL Documentation. https://www.postgresql.org/docs/9.4/functions-info.html
*/