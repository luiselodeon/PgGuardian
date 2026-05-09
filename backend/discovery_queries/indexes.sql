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

/*
 Índice parcial, columna con distribución sesgada
Este query identifica columnas en tablas grandes (>1,000 filas) donde un 
solo valor domina la mayoría de los registros (>85%). Sugiere la creación 
de un índice parcial que excluya dicho valor para optimizar el tamaño del 
índice y acelerar drásticamente las búsquedas del grupo minoritario.
*/
SELECT 
    s.tablename AS table_name,  -- esquema donde reside la tabla
    s.attname AS column_name,  -- tabla analizada
    c.reltuples::bigint AS estimated_rows,  -- columna con sesgo estadístico
    
    /* Valor que domina la columna (el más frecuente)
    forzamos a postgres a convertir el contenido polimórfico en una representación de texto '::text', 
    rompiendo la restricción de anyarray, después esa cadena la convertimos en un array explícito '::text[]',
    text[] sí soporta el operador de acceso por índice, a diferencia de anyarray,
    y extraemos el primer elemento (más frecuente) '[1]'
    */
    (s.most_common_vals::text::text[])[1] AS dominant_value,
    

    -- Porcentaje de filas que tienen ese valor dominante
    round( (s.most_common_freqs[1] * 100)::numeric, 2) AS dominant_pct,

    -- Cuántos valores distintos tiene la columna (contexto)
    s.n_distinct AS estimated_distinct

FROM pg_stats s 
-- join con pg_class para obtener reltuples (estimación del planner)
JOIN pg_class c ON c.relname = s.tablename 
-- join con pg_namespace para asegurar mismo schema y filtrar sistema
JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = s.schemaname 
WHERE 
-- Solo schemas de usuario
    s.schemaname NOT LIKE 'pg_%'
    AND s.schemaname <> 'information_schema'
    AND c.reltuples > 10000  -- filtrar tablas que consideramos pequeñas (< 10000 filas)
    -- Debe tener estadísticas de frecuencia (protección contra NULLs)
    AND s.most_common_freqs IS NOT NULL
    AND array_length(s.most_common_freqs, 1) > 0
    AND s.most_common_freqs[1] > 0.85   -- el valor debe dominar más del 85% de la tabla

/*    
Confirmar que no exista un índice parcial para esa columna.
El query principal encuentra una columna que debería tener un índice parcial (porque un valor domina el 85% de las filas).
- Luego entra el NOT EXISTS y revisa todos los índices que ya existen para esa tabla.
- Usa pg_get_expr para leer qué dicen las condiciones WHERE de esos índices.
- Si encuentra que ya hay un índice parcial que usa esa columna, el NOT EXISTS se vuelve falso y elimina ese resultado del reporte
*/
    AND NOT EXISTS (SELECT 1 FROM pg_index i 
                    WHERE i.indrelid = c.oid
                    AND pg_get_expr(i.indpred, i.indrelid) ILIKE '%' || s.attname || '%')
ORDER BY s.most_common_freqs[1] DESC; -- ordena priorizando los casos de mayor sesgo a menor


/*
Referencias:
PostgreSQL. (2026). 54.1. pg_stats. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/current/view-pg-stats.html
PostgreSQL. (2026). 36.2.5. Polymorphic Types https://www.postgresql.org/docs/current/extend-type-system.html#EXTEND-TYPES-POLYMORPHIC
PostgreSQL. (2026). 9.19. Array Functions and Operators https://www.postgresql.org/docs/current/functions-array.html
PostgreSQL. (2026). 53.26. pg_index. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/catalog-pg-index.html
PostgreSQL. (2026). 9.27. System Information Functions (pg_get_expr). PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/functions-info.html
PostgreSQL. (2026). 9.7. Pattern Matching (ILIKE). PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/functions-matching.html
PostgreSQL. (2026). 9.4. String Functions and Operators (Concatenation). PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/functions-string.html
*/

