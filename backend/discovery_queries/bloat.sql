/*
PgGuardian — Detección de Bloat

En esta sección se documentan los queries con los cuales se encontraron 
problemas de mantenimiento y espacio desperdiciado, utilizando 
el ratio de dead tuples para identificar tablas con bloat severo 
y detectando configuraciones de autovacuum desactivadas 
a nivel de tabla.
*/

/*Se instala la extensión pgstattuple que sirve para analizar el almacenamiento
físico de tablas e índices cuantificando el bloat y la fragmentación de datos

Referencia: Neon. (s. f.). The pgstattuple extension. Neon. https://neon.com/docs/extensions/pgstattuple
*/
CREATE EXTENSION IF NOT EXISTS pgstattuple;

/*El siguiente query está adaptado del query de Greg Sabino Mullane dónde estima el
bloat entre tablas y columnas. Fue adaptado con el fin de asegurar 0 falsos positivos

Referencias:
52.11. pg_class. (2026, 26 febrero). PostgreSQL Documentation. https://www.postgresql.org/docs/current/catalog-pg-class.html
Check_postgres.pl. (s. f.). https://bucardo.org/check_postgres/check_postgres.pl.html#bloat
Ioguix. (2022). pgsql-bloat-estimation/table/table_bloat.sql at master · ioguix/pgsql-bloat-estimation. GitHub. https://github.com/ioguix/pgsql-bloat-estimation/blob/master/table/table_bloat.sql
Posts, V. M. (2020, 18 mayo). Common administrator responsibilities on Amazon RDS and Amazon Aurora for PostgreSQL databases. TargetSocialMedia. https://targetsocialmediasoftware.wordpress.com/2020/05/18/common-administrator-responsibilities-on-amazon-rds-and-amazon-aurora-for-postgresql-databases/
Show database bloat - PostgreSQL wiki. (s. f.). https://wiki.postgresql.org/wiki/Show_database_bloat
*/

/*Significado de columnas:
current_database: nombre de la base de datos dónde se está ejecutando la consulta
shemaname: nombre del esquema
tblname: nombre de la tabla
real_size: tamaño físico actual de la tabla
fillfactor: espacio que se reserva en cada página para futuras actualizaciones
extra_size: espacio en bytes que excede el mínimo teorico absoluto
extra_pct: procentaje de ese extra
bloat_size: espacio desperdiciado en bytes
bloat_pct: porcentaje del bloat
is_na: significado de la estimación si es true no es confiable, si es false es confiable*/

SELECT current_database(), schemaname, tblname, bs*tblpages AS real_size,
  (tblpages-est_tblpages)*bs AS extra_size,
  CASE WHEN tblpages > 0 AND tblpages - est_tblpages > 0
    THEN 100 * (tblpages - est_tblpages)/tblpages::float
    ELSE 0
  END AS extra_pct, fillfactor,
  CASE WHEN tblpages - est_tblpages_ff > 0
    THEN (tblpages-est_tblpages_ff)*bs
    ELSE 0
  END AS bloat_size,
  CASE WHEN tblpages > 0 AND tblpages - est_tblpages_ff > 0
    THEN 100 * (tblpages - est_tblpages_ff)/tblpages::float
    ELSE 0
  END AS bloat_pct, is_na
FROM (
  SELECT ceil( reltuples / ( (bs-page_hdr)/tpl_size ) ) + ceil( toasttuples / 4 ) AS est_tblpages,
    ceil( reltuples / ( (bs-page_hdr)*fillfactor/(tpl_size*100) ) ) + ceil( toasttuples / 4 ) AS est_tblpages_ff,
    tblpages, fillfactor, bs, tblid, schemaname, tblname, heappages, toastpages, is_na
  FROM (
    SELECT
      ( 4 + tpl_hdr_size + tpl_data_size + (2*ma)
        - CASE WHEN tpl_hdr_size%ma = 0 THEN ma ELSE tpl_hdr_size%ma END
        - CASE WHEN ceil(tpl_data_size)::int%ma = 0 THEN ma ELSE ceil(tpl_data_size)::int%ma END
      ) AS tpl_size, bs - page_hdr AS size_per_block, (heappages + toastpages) AS tblpages, heappages,
      toastpages, reltuples, toasttuples, bs, page_hdr, tblid, schemaname, tblname, fillfactor, is_na
    FROM (
      SELECT
        tbl.oid AS tblid, ns.nspname AS schemaname, tbl.relname AS tblname, tbl.reltuples,
        tbl.relpages AS heappages, coalesce(toast.relpages, 0) AS toastpages,
        coalesce(toast.reltuples, 0) AS toasttuples,
        coalesce(substring(
          array_to_string(tbl.reloptions, ' ')
          FROM 'fillfactor=([0-9]+)')::smallint, 100) AS fillfactor,
        current_setting('block_size')::numeric AS bs,
        CASE WHEN version()~'mingw32' OR version()~'64-bit|x86_64|ppc64|ia64|amd64' THEN 8 ELSE 4 END AS ma,
        24 AS page_hdr,
        23 + CASE WHEN MAX(coalesce(s.null_frac,0)) > 0 THEN ( 7 + count(s.attname) ) / 8 ELSE 0::int END
           + CASE WHEN bool_or(att.attname = 'oid' and att.attnum < 0) THEN 4 ELSE 0 END AS tpl_hdr_size,
        sum( (1-coalesce(s.null_frac, 0)) * coalesce(s.avg_width, 0) ) AS tpl_data_size,
        bool_or(att.atttypid = 'pg_catalog.name'::regtype)
          OR sum(CASE WHEN att.attnum > 0 THEN 1 ELSE 0 END) <> count(s.attname) AS is_na
      FROM pg_attribute AS att
        JOIN pg_class AS tbl ON att.attrelid = tbl.oid
        JOIN pg_namespace AS ns ON ns.oid = tbl.relnamespace
        LEFT JOIN pg_stats AS s ON s.schemaname=ns.nspname
          AND s.tablename = tbl.relname AND s.inherited=false AND s.attname=att.attname
        LEFT JOIN pg_class AS toast ON tbl.reltoastrelid = toast.oid
      WHERE NOT att.attisdropped
        AND tbl.relkind in ('r','m')
      GROUP BY 1,2,3,4,5,6,7,8,9,10
      ORDER BY 2,3
    ) AS s
  ) AS s2
) AS s3

-- Muestra los datos que solo sean ciertos
WHERE is_na = false
ORDER BY schemaname, tblname;

/*También se puede tener problemas con el AUTOVACUUM pues esto indica un crecimiento descontrolado del disco, alto uso de CPU/IO
Es fundamental para limpar filas muertas*/

/*La siguiente query nos muestra las tablas que tienen desactivado el AUTOVACUUM

Referencias:
52.11. pg_class. (2026, 26 febrero). PostgreSQL Documentation. https://www.postgresql.org/docs/current/catalog-pg-class.html
LibreByte. (2023, 5 mayo). PostgreSQL  - Optimice sus bases de datos con esta herramienta. [Vídeo]. YouTube. https://www.youtube.com/watch?v=VmuHANA2PFY
Schönig, H.-J. (2021, junio). Enabling and disabling autovacuum in PostgreSQL. CYBERTEC. https://www.cybertec-postgresql.com/en/enabling-and-disabling-autovacuum-in-postgresql/
*/

/*Significado de columnas:
relname: nombre de la tabla
reloptions: campo de texto que guarda configuraciones especificas
*/

SELECT relname, reloptions
FROM pg_class -- catalogo del sistema donde estan las relaciones
WHERE reloptions::text LIKE '%autovacuum_enabled=false%'; -- convertimos el array a texto para poder buscar en el

/*El siguiente query muestra las tablas con muchas filas muertas y que necesitan VACUUM
Referencias:
52.11. pg_class. (2026, 26 febrero). PostgreSQL Documentation. https://www.postgresql.org/docs/current/catalog-pg-class.html
Mitra, N. (2025, 28 marzo). PostgreSQL Performance Optimization — Cleaning Dead Tuples & Reindexing. Medium. https://towardsdev.com/postgresql-performance-optimization-cleaning-dead-tuples-reindexing-9b1346408b97
*/

/*Significado de columnas:
shemaname: nombre del esquema
relname: nombre de la tabla
n_live_tup: filas vivas
n_dead_tup: filas muertas
dead_tuple_pct: porcentaje de filas muertas con respecto a las vivas
*/

SELECT
    schemaname,
    relname AS table_name,
    n_live_tup,
    n_dead_tup,
    CASE
        WHEN n_live_tup + n_dead_tup > 0
        THEN ROUND((n_dead_tup::numeric / (n_live_tup + n_dead_tup) * 100), 2)
        ELSE 0
    END AS dead_tuple_pct
FROM pg_stat_user_tables
ORDER BY dead_tuple_pct DESC;

/*Analisis de resultados:
0%-10% estado optimo
11%-20% estado normal
>20% estado alarmante*/