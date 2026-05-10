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