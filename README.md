# PgGuardian

## Resumen Ejecutivo
**PgGuardian** es un producto B2B de auditoría continua para PostgreSQL en producción. Se conecta únicamente de forma de lectura a la base de datos del cliente y entrega un reporte priorizado con hallazgos accionables en cinco categorías: índices, bloat, queries problemáticas, configuración y salud general.

El producto está dirigido a empresas medianas mexicanas y latinoamericanas que tienen Postgres en producción, pero carecen de un DBA dedicado. Estos equipos típicamente tienen 5-50 desarrolladores, una o dos bases de datos críticas, y resuelven problemas de performance reactivamente cuando ya impactaron al cliente.

**Nuestra Propuesta de Valor:**
A diferencia de alternativas en el mercado (como pganalyze o Datadog), PgGuardian se posiciona como una opción:
* **Accesible:** USD 49/mes por instancia.
* **Localizada:** Interfaz y soporte en español, con recomendaciones que consideran la regulación local.
* **Self-hosted opcional:** Crucial para empresas como fintechs que por seguridad o regulación no pueden enviar metadata de su BD a un proveedor en el extranjero.

---

## Funcionalidades Core

| Feature | Beneficio para el usuario |
| :--- | :--- |
| **Índices inteligentes** | Detecta índices duplicados, índices no usados que solo consumen espacio, y índices faltantes con llaves foráneas. Sugiere la creación de índices en tablas donde se tenga datos grandes y un solo valor domine la mayoría de los registros, y en tablas donde se recomienda usar *Covering Index*. Busca estadísticas obsoletas; al usarlo el usuario ahorra horas de análisis manual. |
| **Control de bloat** | Calcula el porcentaje de espacio desperdiciado en tablas debido a filas muertas. Verifica tablas donde se tenga el AUTOVACUUM desactivado. El usuario recupera almacenamiento y evita que las consultas masivas se vuelvan lentas por escanear páginas vacías. |
| **Optimización de memoria** | Identifica queries que tienen un `work_mem` bajo, evalúa el uso de archivos temporales, valida la configuración contra el workload observado y genera hallazgos y recomendaciones. Reduce la latencia en operaciones complejas. |
| **Monitoreo de conexiones problemáticas** | Identifica conexiones *idle in transaction*, conexiones abandonadas, transacciones largas que retienen locks y tablas que necesiten de particionamiento siguiendo un conjunto de características predefinidas. Ajusta timeouts antes de que derriben la base de datos. |
| **Reporte** | Entrega un reporte con los problemas a los que se enfrenta la base de datos analizada con los features antes mencionados. Incluye un dashboard donde se ve el estado de salud en el que se encuentra la BD y, adicionalmente, cada uno de nuestros features tiene un apartado en donde se pueden ver con más detalle los posibles hallazgos de problemas. |

---

## Instalación y Configuración

### 1. Clonar el repositorio
Abrir una terminal en cualquier ruta de su preferencia e ingresar:
```
git clone https://github.com/luiselodeon/PgGuardian.git
```
```
cd PgGuardian
```

### 2. Crear archivo .env en la raíz del proyecto con los siguientes valores
```
DB_NAME=tiendadb
DB_USER=tienda_user
DB_PASSWORD=tienda_pass
DB_PORT=5433
```


### 3. Levantar Docker
```
docker compose up -d
```

### 4. Ligas de acceso

**Backend API:**    http://localhost:8000/docs
<br>
**Frontend:**       http://localhost:5173
<br> 
**Landing page:** https://landing-page-pg-guardian.vercel.app/
**Liga del video demo** https://youtu.be/Xy6WHuwOaY0

