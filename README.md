[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/JSelemin/nyt_bestsellers_webscraper/blob/main/README.en.md)

# NYT Best Sellers Data Pipeline
 
Pipeline de web scraping que recopila 3 años de datos semanales de los Best Sellers del NYT usando BeautifulSoup y requests, con hashing MD5 para deduplicar libros en más de 150 snapshots semanales. Luego carga los datos en un esquema de estrella en SQLite y los conecta a Power BI, permitiendo análisis de trayectorias de ranking, tendencias de frecuencia por autor y visualizaciones de longevidad en la lista.
 
## Qué hace este proyecto
 
Cada semana, el New York Times publica su lista de Best Sellers de ficción y no ficción. Este pipeline recopila 156 semanas de esos datos (2023–2026), los limpia y deduplica, y los carga en una base de datos con esquema de estrella. El dataset resultante registra qué libros aparecieron en la lista, cuándo, con qué ranking y durante cuánto tiempo, lo que permite analizar la dinámica de la lista a lo largo del tiempo.
 
## Tech Stack
 
- Python
- MS Power BI
- requests
- BeautifulSoup
- pandas
- SQLite
 
## Arquitectura
 
```
NYTimes Best Sellers (HTML)
        ↓
    scraper.py       ← requests + BeautifulSoup, one week at a time
                       rate-limited (1.5s/request), error-handled per week
        ↓
  pandas DataFrames  ← MD5 hash deduplication, null handling for missing links
        ↓
    loader.py        ← explicit SQLite schema, INSERT OR IGNORE
        ↓
  bestsellers.db     ← dim_books + fact_rankings
        ↓
  Power BI (ODBC)    ← dashboards and analysis
```

## Schema
 
La base de datos usa un esquema de estrella simple con una tabla de dimensión y una tabla de hechos.
 
```sql
CREATE TABLE IF NOT EXISTS books (
    hash_id         TEXT PRIMARY KEY,   -- MD5(title|author)
    title           TEXT,
    author          TEXT,
    upc             TEXT,               -- ISBN-13, nullable (not all books have Apple Books links)
    bookshop_url    TEXT
);
 
CREATE TABLE IF NOT EXISTS rankings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    hash_id     TEXT NOT NULL REFERENCES books(hash_id),
    date        TEXT NOT NULL,
    rank        INTEGER NOT NULL,
    UNIQUE(hash_id, week_date)          -- prevents duplicates on re-run
);
```
 
#### Key design decisions

- El `hash_id` se deriva de `MD5(title|author)` en lugar de un identificador scrapeado. Esto garantiza que un libro sea tratado como la misma entidad en las 156 semanas, independientemente de inconsistencias menores en el scraping o de libros que pertenezcan a sagas.
- El UPC vive únicamente en `books` y no en `rankings`, ya que es un atributo del libro y no del evento de ranking.
- `INSERT OR IGNORE` combinado con la restricción  `UNIQUE` sobre `(hash_id, week_date)` hace que el loader sea idempotente: se puede ejecutar múltiples veces sin crear duplicados.

## Configuración
 
**Requirements**

```
pip install requirements.txt
```
 
**Run the pipeline**

```bash
python main.py
```
 
Esto ejecuta scraper → transform → loader en secuencia. Esperar aproximadamente 10 minutos para el backfill histórico completo de 3 años debido al rate limiting. El progreso se imprime por semana.
 
**Conectar a Power BI**
1. Instalar el driver ODBC de SQLite y cargar la base de datos en `data/NYT_bestsellers.db`
2. En Power BI Desktop: Obtener datos → ODBC → apuntar a la base de datos
3. Cargar ambas tablas y definir la relación sobre `hash_id` si Power BI no lo hace automáticamente.
 
## Hallazgos
 
**La longevidad requiere un rendimiento sostenido.** Los libros con más de 40 semanas en la lista promediaron consistentemente entre el ranking 4 y el 9. Ningún libro de larga permanencia tuvo un ranking promedio peor que 10, lo que sugiere que los libros que caen al fondo de la lista tienden a salir rápidamente en lugar de quedarse.
 
**Emergieron dos estrategias de dominancia distintas.** *The Housemaid* (Freida McFadden) entró en el ranking 14 en noviembre de 2023 y se convirtió en el título de mayor permanencia del dataset: 124 semanas con un ranking promedio de 9, sostenido por una escalada gradual más que por un impacto inmediato. Danielle Steel, en cambio, colocó aproximadamente 20 títulos distintos en la lista durante el mismo período, dominando por volumen en lugar de por longevidad individual de cada libro.
 
## Limitaciones
 
- **Fragilidad de los selectores CSS**: el scraper apunta a nombres de clase autogenerados (por ejemplo, `css-1u6k25n`) que se romperán si NYT actualiza su frontend. Un enfoque más robusto usaría selectores estructurales o monitoreo de cambios en los selectores.
- **Lista única**: el pipeline actualmente apunta solo a la lista combinada de ficción impresa y digital. El esquema podría soportar múltiples listas mediante una columna `list_name`, extendiendo el alcance a no ficción o listas por género con cambios mínimos.
- **Actualizaciones incrementales**: el pipeline actual hace un backfill histórico completo. Agregar una tabla `pipeline_metadata` para registrar la última semana cargada lo haría re-ejecutable en un schedule semanal (cron o Task Scheduler).
- **Scheduling**: sin programar por ahora. Una versión productiva correría semanalmente.