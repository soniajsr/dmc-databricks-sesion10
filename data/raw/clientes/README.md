# Datos fuente sintéticos: clientes

Mismos CSVs de la Sesión 09. `transformations/bronze/clientes.py` los lee con Auto Loader
desde la carpeta de landing de cada target (`bundle.landing_path`). Se pueden regenerar con
`data/raw/clientes/gen_clientes.py` si quieres ajustar el volumen o los errores.

## Lotes

| Archivo | Filas | Contenido |
|---|---|---|
| `lote_01_clientes_2024-01-15.csv` | 40 | Clientes nuevos `id_cliente` 1-39 + 1 fila con `id_cliente` vacío |
| `lote_02_clientes_2024-02-12.csv` | 29 | Clientes nuevos 40-59 + segunda fila del 45 con fecha no parseable + 8 actualizaciones a IDs del lote 1 |
| `lote_03_clientes_2024-03-10.csv` | 23 | Clientes nuevos 60-74 + segunda fila del 68 (fecha futura) y del 71 (fecha < 1900) + 6 actualizaciones (algunas sobre IDs ya actualizados en el lote 2) |

Cada target lee de su propia carpeta de landing, dentro de su propio catalog:

| Target | Carpeta de landing |
|---|---|
| `dev` | `/Volumes/dbassociate_dev/default/vol_landing/input/` |
| `test` | `/Volumes/dbassociate_test/default/vol_landing/input/` |
| `prod` | `/Volumes/dbassociate_prod/default/vol_landing/input/` |

Los tres lotes se pueden subir juntos: Silver ordena los cambios por la fecha del lote que
trae el nombre de cada archivo, así que una sola corrida llega al mismo resultado que la
Sesión 09 lote a lote (Bronze 92, Silver 75, Gold 42 filas con 72 clientes).

## Cómo subirlos al volume

El catalog y su volume `vol_landing` se crean antes (Pasos 4 y 6 de `sesion10_setup.ipynb`).

```bash
databricks fs cp data/raw/clientes/lote_01_clientes_2024-01-15.csv \
  dbfs:/Volumes/dbassociate_dev/default/vol_landing/input/ --profile <tu-perfil>
```

Repite con los otros dos lotes. No copies la carpeta entera: `README.md` y
`gen_clientes.py` quedarían en la landing y Auto Loader intentaría leerlos como CSV.

Desde el Web Terminal de un workspace, la copia es un `cp` común:
`cp data/raw/clientes/*.csv /Volumes/dbassociate_test/default/vol_landing/input/`.

## La fila con `id_cliente` vacío

`lote_01` trae a propósito una fila sin `id_cliente` para disparar el warning
`warning_id_cliente_null`. Como la expectation es de tipo warning, la fila pasa a Silver
con la llave en NULL y llega hasta Gold. El schema de Silver declara
`id_cliente BIGINT NOT NULL`, pero la tabla destino del `AUTO CDC` queda con la columna
nullable, así que esa restricción no la frena. Para descartarla antes del CDC, cambia la
regla a `expect_or_drop`; para detener la actualización, a `expect_or_fail`. El
comportamiento es el mismo en cada target al que promuevas el pipeline.

## Filas repetidas dentro de un mismo lote

Los clientes 45 (lote 2), 68 y 71 (lote 3) aparecen dos veces en el mismo archivo. El
`sequence_by` del `AUTO CDC` es `updated_at`, que Silver arma con la fecha del lote que
trae el nombre del archivo. Entre lotes eso ordena bien los cambios, aunque se procesen los
tres en una sola corrida; dentro de un mismo archivo, las dos filas empatan y no hay
garantía de cuál queda como vigente. En la corrida de validación ganó la segunda fila de
cada par.
