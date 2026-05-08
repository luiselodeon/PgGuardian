/*
PgGuardian — Detección de Índices

En esta sección se documentan los queries con los cuales se encontraron 
ineficiencias en la estructura de indexación, tales como 
índices duplicados, índices con nulo uso en pg_stat_user_indexes, 
la ausencia de índices en llaves foráneas que provocan escaneos secuenciales.
*/


-- Buscador de indices duplicados usando pg_index

/*  GLOSARIO
- indrelid: tabla
- indkey: columnas indexadas
- indclass: tipo de índice por columna
- indoption: opciones del índice
- indexprs: expresiones si es un índice por expresión
- indpred: condicion si es un índice parcial
*/
SELECT
-- convierte el oid de la tabla (indrelid) a su nombre legible (con regclass)
    indrelid::regclass AS table_name,
    -- indexrelid: OID del indice
    array_agg(indexrelid::regclass) AS duplicate_indexes, -- agrupa los oids de índices (indexrelid) en un array de nombres legibles
    indkey AS column_ids    -- muestra los ids de las columnas usadas por el índice
-- lee la vista interna de pg_dex, tiene una fila por cada índice creado en la db
FROM pg_index
GROUP BY indrelid, indkey, indclass, indoption, indexprs, indpred   -- agrupa las filas de pg_index por todas las partes que defunen un índice
HAVING COUNT(*) > 1;    -- filtra los que tienen más de una fila, índices duplicados

/* resultado esperado: 
table_name: la tabla afectada
duplicate_indexes: los índices duplicados sobre esa tabla
column_ids: las columnas del índice duplicado
*/
/*
REFERENCIAS:
https://www.postgresql.org/docs/current/datatype-oid.html
https://www.postgresql.org/docs/current/catalog-pg-index.html
https://www.postgresql.org/docs/current/functions-aggregate.html

*/



-- Detector de índices no utilizados
-- los indices no usados consumen espacio sin aprtar nada
SELECT 
    schemaname AS schema_name,
    relname AS table_name,  -- nombre de la tabla a la que pertenece el índice
    indexrelname AS index_name, 
    idx_scan AS total_scans,    -- veces que se ha usado el índice
    -- pg_relation_size(indexrelid): devuelve el tamaño del índice (en bytes)
    -- pg_size_pretty(): convierte el tamaño en formato legible (kb, mb)
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size  
-- usa la vista estadística de índices creada por PostgreSQL, que muestra el número de veces que cada índice ha sido escaneado (idx_scan)
FROM pg_stat_user_indexes
WHERE idx_scan = 0 -- filtra indices que no han tenido usos
    AND relname NOT LIKE 'pg_%' -- exluye objetos que comiencen con pg_ (suelen ser del sistema), deberíamso ver  tablas más relevantes
ORDER BY pg_relation_size(indexrelid) DESC; -- ordena por tamaño del índice, para ver los más costosos primero

/*
Resultado esperado:
schema_name: esquema de la tabla
table_name: tabla asociada
index_name: nombre del índice
total_scans: 0
index_size: tamaño del índice en formato legible
*/

/*
REFERENCIAS:
https://www.postgresql.org/docs/current/ddl-schemas.html
https://www.postgresql.org/docs/current/spi-spi-getrelname.html
https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ALL-INDEXES-VIEW
https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADMIN-SIZE
https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADMIN-STATISTICS-TABLES
https://www.postgresql.org/docs/current/catalog-pg-index.html
*/