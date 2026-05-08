/*
PgGuardian — Detección de Performance

En esta sección se documentan los queries con los cuales se encontraron 
cuellos de botella en la ejecución, analizando las estadísticas de 
pg_stat_statements y planes EXPLAIN para hallar discrepancias en la 
estimación de filas y consultas con alto impacto en disco.
*/


/*
Problema: Detección de Queries que estén usando Seq Scan 

Este query tiene como objetivo principal identificar los queries 
que estén utilizando Seq Scan en la base de datos. Esto lo hace 
mediante la detección de los queries que más tiempo están tomando 
para que en el script de queries.py se pueda detectar si es que 
estos queries tardados estén haciendo uso de seq scan.

Referencias:
PostgreSQL. (2026). F.32. pg_stat_statements — track statistics of SQL planning and execution . PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/pgstatstatements.html
*/

SELECT     
    queryid,
    query, -- El query que se realizó
    calls, -- Número de veces que se ha ejecutado el query
    total_exec_time AS total_time -- Tiempo total acumulado del query 
FROM 
    pg_stat_statements
WHERE 
    query NOT LIKE 'SELECT pg_%' AND query NOT LIKE 'EXPLAIN %' -- Excluimos consultas de catálogo interno y evitamos que se analice a sí mismo
ORDER BY 
    total_exec_time DESC -- Queries que más tiempo tardan
LIMIT 20;