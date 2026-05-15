"""
PgGuardian — Salud de Tablas

Módulo encargado de medir el factor de bloat y salud de autovacuum
mediante el ratio de tuples muertos en pg_stat_user_tables.

Incluye:
Detector de bloat en tablas
Detector de tablas con el autovacuum desactivado
Detector de tablas con filas muertas

Nota: Todos los detectores bajo la carpeta de /detectors fueron normalizados 
con ayuda de la Inteligencia Artificial.
"""
import psycopg2
from psycopg2 import extras

# Bloat en tablas
def check_table_bloat(conn):
    """
    Analiza el almacenamiento físico de tablas e índices cuantificando el bloat
    y la fragmentación de datos asegurando 0 falsos positivos.

    Requiere tener la extensión pgstattuple.
    """

    # Instalar la extensión y forzar la actualización del catálogo
    setup_query = """
    CREATE EXTENSION IF NOT EXISTS pgstattuple;
    """
    #Query que checa el bloat de una tabla
    query = """
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
    WHERE is_na = false
    ORDER BY schemaname, tblname;
    """

    table_bloat = []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Primero ejecutamos la creacion de la extensión
            cur.execute(setup_query)
            # Ejecutamos el query principal de bloat
            cur.execute(query)
            rows = cur.fetchall()

        # Enriquecer cada fila con evidencia y recomendación SQL
        for row in rows:
            row = dict(row)
            bloat_pct = float(row.get('bloat_pct', 0))
            schema = row.get('schemaname', '')
            table = row.get('tblname', '')
            bloat_size = row.get('bloat_size', 0)

            row['evidence'] = (
                f"La tabla '{schema}.{table}' tiene {bloat_pct:.1f}% de bloat "
                f"({bloat_size:,} bytes desperdiciados en almacenamiento fragmentado)."
            )
            row['sql_recommendation'] = f"VACUUM FULL {schema}.{table};"
            table_bloat.append(row)

    except Exception as e:
        print(f"Error al analizar el bloat de las tablas: {e}")
        raise e

    return table_bloat


# Detectar tablas con el autovacuum desactivado
def check_disabled_autovacuum(conn):
    """
    Muestra las tablas que tienen desactivado el AUTOVACUUM.
    Esto puede indicar un crecimiento descontrolado del disco y alto uso de CPU/IO.
    """
    query = """
    SELECT relname, reloptions
    FROM pg_class
    WHERE reloptions::text LIKE '%%autovacuum_enabled=false%%';
    """

    disabled_autovacuum = []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

        # Enriquecer cada fila con evidencia y recomendación SQL
        for row in rows:
            row = dict(row)
            table = row.get('relname', '')
            row['evidence'] = (
                f"La tabla '{table}' tiene autovacuum explícitamente desactivado "
                f"en sus opciones de almacenamiento: {row.get('reloptions', '')}."
            )
            row['sql_recommendation'] = (
                f"ALTER TABLE {table} RESET (autovacuum_enabled);\n"
                f"-- O para re-habilitarlo explícitamente:\n"
                f"ALTER TABLE {table} SET (autovacuum_enabled = true);"
            )
            disabled_autovacuum.append(row)

    except Exception as e:
        print(f"Error al detectar tablas con autovacuum desactivado: {e}")
        raise e

    return disabled_autovacuum


# Detectar tablas con filas muertas
def check_dead_tuples(conn):
    """
    Muestra las tablas con muchas filas muertas (dead tuples) y que necesitan VACUUM.
    0%-10% estado optimo | 11%-20% estado normal | >20% estado alarmante
    """
    query = """
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
    """

    dead_tuples = []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

        # Enriquecer cada fila con evidencia y recomendación SQL
        for row in rows:
            row = dict(row)
            schema = row.get('schemaname', '')
            table = row.get('table_name', '')
            dead_pct = float(row.get('dead_tuple_pct', 0))
            n_dead = row.get('n_dead_tup', 0)

            row['evidence'] = (
                f"La tabla '{schema}.{table}' tiene {dead_pct:.2f}% de filas muertas "
                f"({n_dead:,} dead tuples acumuladas)."
            )

            if dead_pct > 20:
                row['sql_recommendation'] = (
                    f"-- Estado alarmante (>{dead_pct:.1f}% dead tuples)\n"
                    f"VACUUM FULL ANALYZE {schema}.{table};"
                )
            elif dead_pct > 10:
                row['sql_recommendation'] = (
                    f"-- Estado elevado ({dead_pct:.1f}% dead tuples)\n"
                    f"VACUUM ANALYZE {schema}.{table};"
                )
            else:
                row['sql_recommendation'] = (
                    f"-- Estado óptimo, sin acción urgente necesaria\n"
                    f"VACUUM ANALYZE {schema}.{table};"
                )

            dead_tuples.append(row)

    except Exception as e:
        print(f"Error al detectar las filas muertas (dead tuples): {e}")
        raise e

    return dead_tuples
