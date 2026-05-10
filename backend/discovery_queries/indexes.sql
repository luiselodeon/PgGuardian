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

/*
Problema: Detección de llaves foráneas sin índice

Este query tiene como objetivo principal identificar las columnas 
que actúan como llaves foráneas que no tienen un indice asociado en 
la tabla donde se encuentra. 

Referencias: 
PostgreSQL. (2026). 52.13. pg_constraint. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/catalog-pg-constraint.html
PostgreSQL. (2026). 52.7. pg_attribute. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/catalog-pg-attribute.html
PostgreSQL. (2026). 52.26. pg_index. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/catalog-pg-index.html
*/

SELECT 
    conname AS constraint_name, -- Nombre de la restricción
    conrelid::regclass AS table_name, -- La tabla donde está la FK
    a.attname AS column_name, -- El nombre de la columna que es la FK
    confrelid::regclass AS referenced_table, -- La tabla a la que apunta esta FK
    CASE 
        WHEN i.indexrelid IS NOT NULL THEN 'Si'	-- Si es que tiene un índice
        ELSE 'No'
    END AS tiene_indice
FROM 
    pg_constraint c
JOIN 
    pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
LEFT JOIN 
    pg_index i ON i.indrelid = c.conrelid AND a.attnum = i.indkey[0] -- Checa si es la primera columna del índice
WHERE 
    c.contype = 'f' -- Se usa f para filtrar las llaves foráneas
ORDER BY 
    tiene_indice ASC, table_name;


/*
Problema: Índices duplicados

Este query identifica índices que comparten la misma tabla, 
las mismas columnas y el mismo orden, lo cual genera redundancia.
Se excluyen los catálogos de PostgreSQLpara evitar reportar duplicados 
internos del motor. 

Referencias:
PostgreSQL. (2026). 52.7. pg_attribute. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/catalog-pg-attribute.html
PostgreSQL. (2026). 52.26. pg_index. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/catalog-pg-index.html
PostgreSQL. (2026). 52.11. pg_class. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/catalog-pg-class.html
PostgreSQL. (2026). 52.32. pg_namespace. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/catalog-pg-namespace.html
*/

SELECT 
    indrelid::regclass AS table_name, -- Convierte el OID a nombre de tabla
    array_to_string(array_agg(a.attname ORDER BY x.pos), ', ') AS columns, -- Convierte el arreglo de nombres de columnas en una cadena de texto y los agrupa
    COUNT(*) AS total_duplicates,
    string_agg(i.relname, ', ') AS index_names -- Concatena los nombres de los índices duplicados
FROM (
    SELECT -- Subconsulta para desglosar indkey en filas individuales
        indrelid, 
        indexrelid, 
        indkey, 
        generate_subscripts(indkey, 1) AS pos -- Genera indices para cada columna en el índice
    FROM pg_index
) AS x
JOIN pg_attribute a ON a.attrelid = x.indrelid AND a.attnum = x.indkey[x.pos]
JOIN pg_class i ON i.oid = x.indexrelid
JOIN pg_namespace n ON n.oid = i.relnamespace -- Unión para verificar el esquema
WHERE 
    n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast') -- Excluye esquemas del sistema para evitar ruido
GROUP BY indrelid, indkey
HAVING COUNT(*) > 1
ORDER BY table_name;


/*
Problema: Índices no usados

Identifica índices que no han sido utilizados en escaneos (idx_scan = 0)
pero cuyas tablas sí han recibido actividad. El catálogo de pg_stat_user_indexes
proporciona información sobre cómo se está usando la base de datos en la vida 
real. 

Referencias: 
PostgreSQL. (2026). 27.2. The Cumulative Statistics System. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/monitoring-stats.html#MONITORING-STATS-VIEWS
*/

SELECT 
    schemaname AS schema_name,         
    relname AS table_name, -- Nombre de la tabla a la que pertenece el índice.
    indexrelname AS index_name, -- Nombre del índice detectado como no usado.
    idx_scan, 
    pg_size_pretty( 
        pg_relation_size(indexrelid) -- Calcula el espacio físico que el índice ocupa en disco.
    ) AS index_size
FROM 
    pg_stat_user_indexes -- Vista de PostgreSQL que rastrea el uso de índices.
WHERE 
    idx_scan = 0 -- Filtra los índices que nunca se han usado.
    AND idx_tup_read = 0 -- Checar que no se han leído tuplas a través de él.
    AND idx_tup_fetch = 0 -- Checar que no se han obtenido tuplas a través de él.    
    AND indexrelname NOT LIKE '%_pkey' -- Excluye los índices de primary keys para evitar ruido 
ORDER BY 
    pg_relation_size(indexrelid) DESC; -- Ordena por tamaño para conocer los índices que más espacio ocupan.


/*
Covering index con INCLUDE
Identifica consultas de alta frecuencia que filtran por una columna pero proyectan 
otras adicionales. Sugiere la implementación de un "Covering Index" para permitir 
un Index-Only Scan, eliminando la necesidad de acceder al Heap (tabla física) 
y reduciendo drásticamente el I/O.
*/
SELECT 
-- recorte de cadena para no saturar buffers y legilibilidad en reportes
    LEFT(query, 200) AS query_sample, -- muestra de la consulta normalizada
    -- conteo de ejecuciones totales
    calls AS executions,  -- popularidad de la consulta

    -- Tiempo total acumulado en milisegundos
    round(total_exec_time::numeric, 2) AS total_time_ms,
    
    -- tiempo promedio por ejecución. avg = totalTime / calls
    round((total_exec_time / NULLIF(calls, 0))::numeric, 2) AS avg_ms,

    -- cálculo del ratio de cache_hit (eficiencia en RAM)
    -- eficiencia del caché, si es baja, el covering index urge más
    CASE 
        WHEN (shared_blks_hit + shared_blks_read) > 0
            THEN round(100.0 * shared_blks_hit / (shared_blks_hit + shared_blks_read), 2)
        ELSE 100
    END AS cache_hit_pct
FROM pg_stat_statements
WHERE  
    query ILIKE 'SELECT%'   -- filtra solo consultas de lectura
    AND query ~ 'WHERE\s+\S+\s*=\s*\$[0-9]' -- solo queries con criterios de filtrado
    AND query NOT ILIKE 'SELECT *%' -- ignora proyecciones completas (no optimizables con INCLUDE)
    AND query NOT ILIKE 'SELECT count(*)%' -- Excluir COUNT(*) — son aggregations, no proyecciones
    AND calls >= 5   -- ignorar consultas ruidosas
    -- Excluir consultas al catálogo del sistema
    AND query NOT ILIKE '%pg_stat%'
    AND query NOT ILIKE '%pg_class%'
    AND query NOT ILIKE '%pg_index%'
    AND query NOT ILIKE '%information_schema%'
ORDER BY total_exec_time DESC   -- priorizar por carga acumulada
LIMIT 15;

/*
Referencias.
https://www.postgresql.org/docs/18/functions-string.html
https://www.postgresql.org/docs/current/functions-conditional.html#FUNCTIONS-NULLIF
https://www.postgresql.org/docs/current/pgstatstatements.html
https://www.postgresql.org/docs/18/functions-matching.html

*/

/*
Buscar estadísticas obsoletas
Después de inserts o deletes sin analyze, o sin autovacuum
El planner de Postgres usa pg_class.reltuples para estimar cuántas filas leerá cada operación
si hay más filas de las que este detecta, las operaciones serán mucho más lentas
*/

WITH stats_completions AS (
    SELECT
        psu.schemaname AS schema_name,
        psu.relname AS table_name,
        c.reltuples::bigint AS planner_estimate, -- reltuples es lo que el Planner cree que tiene la tabla, solo se actualiza después de un ANALYZE o VACUUM
        psu.n_live_tup AS stats_live_tuples,    -- es lo que el Collector cuenta, se actualiza casi en tiempo real con cada INSERT o DELETE
        CASE
            WHEN psu.n_live_tup > 0 AND c.reltuples > 0 -- mediremos un ratio para estimar que tan desfasado está el planner
                THEN round (
                    /*
                    comparar el más grande contra el más chico por si crece o si se achica
                    - GREATEST: toma el número más grande
                    - LEAST: Selecciona el más pequeño
                    con ::numeric obtenemos decimales de la división, limitamos a 2,
                    con la comparación nos aseguramos que el resultado siempre sea un num > 1
                    */ 
                    GREATEST(c.reltuples, psu.n_live_tup)::numeric / LEAST(c.reltuples, psu.n_live_tup)::numeric, 2)
            ELSE NULL
        END AS divergence_ratio
    FROM pg_stat_user_tables psu
    -- JOIN con pg_namespace para evitar colisiones de nombres entre esquemas
    JOIN pg_class c ON c.relname = psu.relname
    JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = psu.schemaname
    WHERE n.nspname NOT LIKE 'pg_%' -- excluimos las tablas del sistema
    AND c.relkind = 'r' -- buscamos relaciones normales (tablas), no índices, vistas o secuencias
)   
    SELECT *,
        CASE WHEN divergence_ratio > 10 THEN 'CRITICAL'
        WHEN divergence_ratio > 5 THEN 'WARNING'
        ELSE 'OK'
    END AS stats
    FROM stats_completions
    /*
    - Filtro de tablas que han recibido carga de datos pero nunca han sido procesadas por el Autovacuum/Analyze
    - Divergencia > 5 (umbral estándar de riesgo de Seq Scan).
    - (estimate = 0) = tablas nuevas/importadas que no tienen foto inicial 
    */
    -- tolerancia de 5, si el ratio es mayor a eso, un seq scan erróneo puede ocurrir más fácil
    WHERE (divergence_ratio > 5) OR (planner_estimate = 0 AND stats_live_tuples > 100)
    -- Se establece un umbral de 100 tuplas vivas para asegurar Significancia Estadística
    -- En tablas pequeñas, un ratio de divergencia alto es irrelevante.
ORDER BY divergence_ratio DESC NULLS LAST;

/*
REFERENCIAS.
PostgreSQL. (2026). 52.11. pg_class. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/catalog-pg-class.html
PostgreSQL. (2026). 52.32. pg_namespace. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/catalog-pg-namespace.html
PostgreSQL. (2026). 27.2.19. pg_stat_all_tables. PostgreSQL 18 Documentation.  https://www.postgresql.org/docs/18/monitoring-stats.html#MONITORING-PG-STAT-ALL-TABLES-VIEW
PostgreSQL. (2026). 9.3. Mathematical Functions and Operators. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/functions-math.html
PostgreSQL. (2026). 9.18.4. GREATEST and LEAST. https://www.postgresql.org/docs/18/functions-conditional.html#FUNCTIONS-GREATEST-LEAST
PostgreSQL. (2026). 9.18.1. CASE. https://www.postgresql.org/docs/18/functions-conditional.html#FUNCTIONS-CASE
*/

/*
Detector de wildcard
Detecta queries en pg_stat_statements que usan el patrón LIKE '%algo%' (con % al inicio),
Este patrón impide que Postgres use cualquier índice B-Tree (balanced tree que acelera las consultas)
 porque el motor no puede hacer un range scan si no conoce los primeros caracteres de la cadena buscada,
 viéndose forzado a hacer seq scans (mucho más lentos)
*/

SELECT
-- Recorte a 250 caracteres para evitar saturar el reporte
    LEFT(pss.query, 250) AS query_sample,
    pss.calls AS total_executions,
    round(pss.total_exec_time::numeric,2) AS total_time_ms,
    -- tiempo promedio: permite identificar si la query es lenta por naturaleza
    round( (pss.total_exec_time / NULLIF(pss.calls, 0))::numeric, 2 ) AS avg_ms,

    CASE
    -- busca la palabra LIKE seguida de cualquier texto que no sea otra comilla
    -- nos asegura que estemos detectando el comodín al inicio, que es el que realmente rompe el índice
        WHEN pss.query ~* 'LIKE\s+''%[^'']+%'''
            THEN 'LIKE con wildcard inicial: LIKE ''%texto%'' (sensible a mayúsculas)'
        WHEN pss.query ~* 'ILIKE\s+''%[^'']+%'''
            THEN 'ILIKE con wildcard inicial: ILIKE ''%texto%'' (insensible a mayúsculas)'
        ELSE 'Patrón LIKE/ILIKE ineficiente detectado'
    END AS anti_pattern_type,

    -- Clasificación de severidad (Lógica de impacto: Frecuencia x Tiempo)
    CASE
    -- consultas frecuentes (>100 ejecuciones) que además son lentas (>500ms).
        WHEN pss.calls > 100 AND (pss.total_exec_time / NULLIF(pss.calls, 0)) > 500
            THEN 'HIGH'
    -- consultas con latencia alta (>1s) aunque no sean tan frecuentes
        WHEN pss.calls > 50 OR (pss.total_exec_time / NULLIF(pss.calls, 0)) > 1000
            THEN 'MEDIUM'
        ELSE 'LOW'
    END AS severity

FROM pg_stat_statements pss

WHERE
    -- Filtro principal: Detectar LIKE/ILIKE con '%' literal al principio
    -- Caso: LIKE '%...%'
    (pss.query ~* 'LIKE\s+''%[^'']+%''' OR pss.query ~* 'ILIKE\s+''%[^'']+%''')
    -- Caso: ILIKE '%...%'
    
    -- Excluir consultas esporádicas (filtramos ruido de desarrollo)
    AND pss.calls >= 2
    
    -- Excluir consultas de mantenimiento y del sistema
    AND pss.query NOT ILIKE '%pg_stat%'
    AND pss.query NOT ILIKE '%pg_class%'
    AND pss.query NOT ILIKE '%pg_index%'
    AND pss.query NOT ILIKE '%information_schema%'

-- Priorizar por impacto total en el servidor (cpu + I/O)
ORDER BY pss.total_exec_time DESC
LIMIT 15;

/*
REFERENCIAS.

PostgreSQL. (2026). 9.7.3. POSIX Regular Expressions. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/current/functions-matching.html#FUNCTIONS-POSIX-REGEXP
PostgreSQL. (2026). 65.1. B-Tree Indexes. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/current/btree.html
PostgreSQL. (2026). 9.7. Pattern Matching. PostgreSQL 18 Documentation. https://www.postgresql.org/docs/current/functions-matching.html
PostgreSQL. (2026). F.35. pg_trgm (Trigram matching for LIKE). PostgreSQL 18 Documentation. https://www.postgresql.org/docs/current/pgtrgm.html
*/