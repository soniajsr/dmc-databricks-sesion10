import csv
import os

OUT_DIR = r"c:\Users\Usuario\Documents\repositorios_git\GitHub\databricks-professional-sdp\data\raw\clientes"
os.makedirs(OUT_DIR, exist_ok=True)

CIUDADES = ["Lima", "Arequipa", "Trujillo", "Chiclayo", "Piura", "Cusco",
            "Huancayo", "Tacna", "Iquitos", "Pucallpa", "Chimbote", "Ica"]

NOMBRES = [
    "Maria Gonzalez", "Carlos Ramirez", "Ana Torres", "Luis Fernandez", "Patricia Vega",
    "Jorge Quispe", "Rosa Mamani", "Miguel Rojas", "Carmen Flores", "Pedro Huaman",
    "Lucia Salazar", "Diego Castro", "Elena Rios", "Fernando Chavez", "Gabriela Paredes",
    "Ricardo Medina", "Sofia Vargas", "Andres Cardenas", "Valentina Espinoza", "Manuel Aguirre",
    "Daniela Cabrera", "Sebastian Nunez", "Camila Reyes", "Javier Morales", "Isabel Guerrero",
    "Alvaro Delgado", "Paola Ibanez", "Raul Campos", "Veronica Silva", "Hugo Bravo",
    "Natalia Ortiz", "Gustavo Pinto", "Claudia Herrera", "Ivan Suarez", "Monica Villalobos",
    "Oscar Ponce", "Teresa Cordero", "Emilio Zambrano", "Beatriz Solano", "Rodrigo Escobar",
    "Antonio Vera", "Karina Leon", "Julio Paz", "Milagros Cruz", "Victor Alarcon",
    "Susana Bermudez", "Freddy Cotrina", "Yolanda Nina", "Marco Estrada", "Silvia Ochoa",
]

DOMINIOS = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com"]

def email_for(nombre, idx, upper=False, literal_null=False, broken=False):
    if literal_null:
        return "null"
    base = nombre.lower().replace(" ", ".")
    dom = DOMINIOS[idx % len(DOMINIOS)]
    if broken:
        return f"{base.replace('.', '')}{dom}"  # sin @ ni punto separador
    e = f"{base}@{dom}"
    return e.upper() if upper else e

DATE_FORMATS = [
    lambda y, m, d: f"{y:04d}-{m:02d}-{d:02d}",
    lambda y, m, d: f"{d:02d}/{m:02d}/{y:04d}",
    lambda y, m, d: f"{m:02d}-{d:02d}-{y:04d}",
    lambda y, m, d: f"{y:04d}/{m:02d}/{d:02d}",
    lambda y, m, d: f"{y:04d}-{m:02d}-{d:02d} {8 + (d % 10):02d}:{(d*7) % 60:02d}:00",
    lambda y, m, d: f"{d:02d}/{m:02d}/{y:04d} {8 + (d % 10):02d}:{(d*7) % 60:02d}:00",
    lambda y, m, d: f"{m:02d}/{d:02d}/{y:04d}",
]

def fecha_for(idx, y, m, d):
    return DATE_FORMATS[idx % len(DATE_FORMATS)](y, m, d)

HEADER = ["id_cliente", "nombre", "email", "ciudad", "fecha_registro"]

# ---------------- BATCH 1 : 2024-01-15 -> ids 1-39 + 1 fila con id vacio (dirty) ----------------
rows1 = []
for i in range(1, 40):
    idx = i - 1
    nombre = NOMBRES[idx % len(NOMBRES)]
    # variar casing/espacios para probar initcap/trim
    if i % 7 == 0:
        nombre_out = nombre.upper()
    elif i % 5 == 0:
        nombre_out = f"  {nombre.lower()}  "
    else:
        nombre_out = nombre

    ciudad = CIUDADES[idx % len(CIUDADES)]
    ciudad_out = ciudad
    if i in (9, 24):  # ciudad ausente (permitido por diseno, no es "dirty")
        ciudad_out = ""

    email_out = email_for(nombre, idx, upper=(i % 11 == 0))
    if i == 11:
        email_out = email_for(nombre, idx, broken=True)  # dirty: sin @

    y, m, d = 2021 + (idx % 3), 1 + (idx % 12), 1 + (idx % 27)
    fecha_out = fecha_for(idx, y, m, d)

    rows1.append([i, nombre_out, email_out, ciudad_out, fecha_out])

# dirty: id_cliente vacio (NULL) -> dispara warning_id_cliente_null y, ademas,
# rompera el merge AUTO CDC porque el target exige id_cliente NOT NULL (ver README)
rows1.append(["", "Roberto Aliaga", "roberto.aliaga@gmail.com", "Lima", "2024-01-10"])

with open(os.path.join(OUT_DIR, "lote_01_clientes_2024-01-15.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(HEADER)
    w.writerows(rows1)

# ---------------- BATCH 2 : 2024-02-12 -> ids 40-59 nuevos + 8 actualizaciones ----------------
rows2 = []
for i in range(40, 60):
    idx = i - 1
    nombre = NOMBRES[idx % len(NOMBRES)]
    nombre_out = nombre if i % 6 else nombre.upper()
    ciudad = CIUDADES[idx % len(CIUDADES)]
    email_out = email_for(nombre, idx)
    if i == 47:
        email_out = email_for(nombre, idx, literal_null=True)  # dirty: literal "null"
    y, m, d = 2024, 1 + (idx % 2), 1 + (idx % 27)
    fecha_out = fecha_for(idx, y, m, d)
    rows2.append([i, nombre_out, email_out, ciudad, fecha_out])

# dirty: fecha en formato no reconocido -> parse_fecha_registro_safe devuelve NULL
rows2.append([45, NOMBRES[44 % len(NOMBRES)], email_for(NOMBRES[44 % len(NOMBRES)], 44), "Cusco", "15-Ene-2024"])

# actualizaciones a clientes existentes del lote 1 (mismo id_cliente, datos nuevos)
updates_lote1 = [3, 7, 12, 18, 24, 29, 33, 37]
for n, i in enumerate(updates_lote1):
    idx = i - 1
    nombre = NOMBRES[idx % len(NOMBRES)]
    nueva_ciudad = CIUDADES[(idx + 3) % len(CIUDADES)]  # cambia de ciudad
    nuevo_email = email_for(nombre, idx + 1)  # cambia de dominio
    fecha_out = fecha_for(idx + 2, 2024, 2, 5 + n)
    rows2.append([i, nombre, nuevo_email, nueva_ciudad, fecha_out])

with open(os.path.join(OUT_DIR, "lote_02_clientes_2024-02-12.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(HEADER)
    w.writerows(rows2)

# ---------------- BATCH 3 : 2024-03-10 -> ids 60-74 nuevos + 6 actualizaciones ----------------
rows3 = []
for i in range(60, 75):
    idx = i - 1
    nombre = NOMBRES[idx % len(NOMBRES)]
    ciudad = CIUDADES[idx % len(CIUDADES)]
    email_out = email_for(nombre, idx)
    y, m, d = 2024, 2 + (idx % 2), 1 + (idx % 27)
    fecha_out = fecha_for(idx, y, m, d)
    rows3.append([i, nombre, email_out, ciudad, fecha_out])

# dirty: fecha futura (> current_date) -> nulled por regla de rango
rows3.append([68, NOMBRES[67 % len(NOMBRES)], email_for(NOMBRES[67 % len(NOMBRES)], 67), "Piura", "31/12/2099"])
# dirty: fecha anterior a 1900 -> nulled por regla de rango
rows3.append([71, NOMBRES[70 % len(NOMBRES)], email_for(NOMBRES[70 % len(NOMBRES)], 70), "Ica", "1850-06-15"])

# actualizaciones: algunas sobre ids originales del lote 1, otras sobre ids ya
# actualizados en el lote 2 (para mostrar un segundo "salto" de CDC)
updates_lote3 = [3, 45, 50, 8, 55, 20]
for n, i in enumerate(updates_lote3):
    idx = i - 1
    nombre = NOMBRES[idx % len(NOMBRES)]
    nueva_ciudad = CIUDADES[(idx + 5) % len(CIUDADES)]
    nuevo_email = email_for(nombre, idx + 2)
    fecha_out = fecha_for(idx + 4, 2024, 3, 3 + n)
    rows3.append([i, nombre, nuevo_email, nueva_ciudad, fecha_out])

with open(os.path.join(OUT_DIR, "lote_03_clientes_2024-03-10.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(HEADER)
    w.writerows(rows3)

print("OK -", len(rows1), len(rows2), len(rows3))
