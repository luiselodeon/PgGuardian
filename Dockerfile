#Imagen de postgres
FROM postgres:16

# Instalamos lo necesario para utilizar pg_partman
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-16 \
    && rm -rf /var/lib/apt/lists/*

# Bajamos el codigo de github y lo instalamos
RUN git clone https://github.com/pgpartman/pg_partman.git /tmp/pg_partman \
    && cd /tmp/pg_partman \
    && make install \
    && rm -rf /tmp/pg_partman