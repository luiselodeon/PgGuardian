/*
PgGuardian — Detección de Índices

En esta sección se documentan los queries con los cuales se encontraron 
ineficiencias en la estructura de indexación, tales como 
índices duplicados, índices con nulo uso en pg_stat_user_indexes, 
la ausencia de índices en llaves foráneas que provocan escaneos secuenciales.
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