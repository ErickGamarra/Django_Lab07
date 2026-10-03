# Laboratorio 07 — ORM Avanzado: Transacciones Atómicas, Agregaciones Analíticas, QuerySets Personalizados y Rendimiento SQL

**Curso:** Desarrollo de Aplicaciones Empresariales
**Institución:** Tecsup
**Sección:** 4 - C24 - Sección CD
**Docente:** Yunior Bestard Aroche

**Integrantes:**

1. Jesús Enrique Rocha Bobadilla
2. Erick Arturo Gamarra Mundaca

**Proyecto:** UrbanTrend — Plataforma Textil Streetwear y Sistema Logístico Avanzado con Django ORM y SQLite

**Repositorio GitHub:** https://github.com/Jesus-Rocha-B/Django_Lab06.git

---

## 🎯 1. Objetivo del Laboratorio 07

El Laboratorio 06 resolvió el modelado relacional y el CRUD básico sobre el ORM de Django. El Laboratorio 07 da el salto hacia **patrones de concurrencia y persistencia avanzada**: ya no basta con que la aplicación "guarde datos", sino que debe garantizar que lo haga de forma **consistente, segura frente a accesos simultáneos y eficiente a nivel SQL**.

Esta transición se aplica sobre dos dominios del proyecto UrbanTrend:

- **`store` (comercial):** catálogo, ventas y reportes comerciales de prendas streetwear.
- **`logistics` (insumos textiles):** categorías de materiales, fichas técnicas, stock y órdenes de despacho.

Los **5 pilares** del laboratorio son:

- **Integridad ACID con `transaction.atomic()`:** operaciones multi-modelo que se confirman completas o se revierten por completo (*commit* / *rollback*).
- **Prevención de *race conditions* con `F()`:** las actualizaciones de stock se resuelven dentro de la base de datos (`UPDATE ... SET stock = stock - n`), no en memoria de Python.
- **Analítica en base de datos con `aggregate()` / `annotate()`:** totales, promedios y agrupaciones calculados por el motor SQL, no iterando objetos en la vista.
- **Encapsulamiento con `QuerySet.as_manager()`:** reglas de negocio reutilizables y encadenables, definidas una sola vez en el modelo.
- **Eliminación empírica de consultas N+1 con `select_related()`:** medición con `connection.queries` y reducción de `1 + 2N` consultas a una sola con `JOIN`.

---

## 🏗️ 2. Arquitectura de Módulos y Dominio Relacional

### 2.1 Árbol del proyecto

```text
Django_Lab07/
├── requirements.txt
├── manage.py
├── db.sqlite3
└── src/
    ├── core/                              # Configuración del proyecto
    │   ├── __init__.py
    │   ├── settings.py                    # INSTALLED_APPS, DB SQLite, templates
    │   ├── urls.py                        # Enrutador raíz (admin, store, logistics)
    │   ├── asgi.py
    │   └── wsgi.py
    │
    ├── store/                             # Dominio comercial
    │   ├── models.py                      # Producto, Venta (y relacionados)
    │   ├── views.py                       # reportes_view (panel comercial de ventas)
    │   ├── urls.py                        # /reportes/
    │   ├── admin.py
    │   ├── migrations/
    │   └── templates/store/
    │       └── reportes.html              # Panel comercial de ventas
    │
    └── logistics/                         # Dominio logístico de insumos textiles
        ├── models.py                      # Categoria, Material (+ MaterialQuerySet),
        │                                  # FichaTecnica, OrdenDespacho, DetalleDespacho
        ├── views.py                       # despacho_transaccional_view,
        │                                  # reporte_logistica_view, materiales_view
        ├── urls.py                        # /logistics/despacho/transaccional/,
        │                                  # /logistics/reporte/, /logistics/materiales/
        ├── admin.py
        ├── migrations/
        └── templates/logistics/
            ├── despacho_transaccional.html  # Formulario + resultado de la transacción
            ├── reporte.html                 # Dashboard gerencial (KPIs + tablas)
            └── materiales.html              # Catálogo optimizado con select_related
```

### 2.2 Resumen técnico de entidades

| Relación | Entidades | Implementación Django | Descripción |
|:---|:---|:---|:---|
| **1:N** | `Categoria` → `Material` | `ForeignKey(Categoria, related_name='materiales')` | Una categoría (telas, hilos, avíos) agrupa muchos materiales. |
| **1:1** | `Material` → `FichaTecnica` | `OneToOneField(Material, related_name='ficha')` | Cada material posee una única ficha con sus especificaciones técnicas. |
| **N:M intermedio** | `OrdenDespacho` ↔ `Material` mediante `DetalleDespacho` | Modelo intermedio con dos `ForeignKey` y atributos propios | La tabla puente almacena datos históricos del despacho (`cantidad`, `precio_unitario`), que no cambian aunque el material se modifique después. |

```python
class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)


class Material(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="materiales")
    nombre = models.CharField(max_length=120)
    stock = models.PositiveIntegerField(default=0)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    objects = MaterialQuerySet.as_manager()   # Sección 5


class FichaTecnica(models.Model):
    material = models.OneToOneField(Material, on_delete=models.CASCADE, related_name="ficha")
    composicion = models.CharField(max_length=150)
    gramaje = models.PositiveIntegerField(help_text="g/m²")


class OrdenDespacho(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)
    materiales = models.ManyToManyField(Material, through="DetalleDespacho")


class DetalleDespacho(models.Model):
    orden = models.ForeignKey(OrdenDespacho, on_delete=models.CASCADE, related_name="detalles")
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # histórico
```

---

## ⚡ 3. Control de Concurrencia y Transacciones Atómicas (ACID)

La vista `despacho_transaccional_view` registra una orden de despacho que involucra **tres modelos** (`Material`, `OrdenDespacho`, `DetalleDespacho`). Todo ocurre dentro de un bloque `transaction.atomic()`:

- `select_for_update()` bloquea la fila del material hasta que termina la transacción, evitando que otro proceso lea un stock obsoleto.
- `F('stock') - cantidad` delega la resta al motor SQL, eliminando la *race condition* del patrón leer-modificar-guardar en Python.
- `simular_error` es una compuerta de fallo deliberado **después** de las escrituras, para demostrar empíricamente el *rollback*.

```python
from django.db import transaction
from django.db.models import F
from django.shortcuts import render
from .models import Material, OrdenDespacho, DetalleDespacho


def despacho_transaccional_view(request):
    contexto = {"materiales": Material.objects.con_stock()}

    if request.method == "POST":
        material_id = int(request.POST["material"])
        cantidad = int(request.POST["cantidad"])
        simular_error = request.POST.get("simular_error") == "on"

        try:
            with transaction.atomic():
                # 1) Bloqueo pesimista de la fila para esta transacción
                material = Material.objects.select_for_update().get(pk=material_id)

                if material.stock < cantidad:
                    raise ValueError("Stock insuficiente para el despacho.")

                # 2) Cabecera de la orden
                orden = OrdenDespacho.objects.create(codigo=f"OD-{OrdenDespacho.objects.count() + 1:05d}")

                # 3) Detalle con precio histórico
                DetalleDespacho.objects.create(
                    orden=orden,
                    material=material,
                    cantidad=cantidad,
                    precio_unitario=material.precio_unitario,
                )

                # 4) Descuento atómico en la base de datos (sin race condition)
                Material.objects.filter(pk=material.pk).update(stock=F("stock") - cantidad)

                # 5) Compuerta de fallo: fuerza el rollback de los pasos 2, 3 y 4
                if simular_error:
                    raise RuntimeError("Error simulado: se revierte toda la transacción.")

            contexto["resultado"] = f"✅ Orden {orden.codigo} confirmada (COMMIT)."
        except Exception as exc:
            contexto["resultado"] = f"❌ Transacción revertida (ROLLBACK): {exc}"

    return render(request, "logistics/despacho_transaccional.html", contexto)
```

### Comparativa de escenarios

| Aspecto | ✅ Transacción Exitosa (`simular_error=False`) | ❌ Transacción Fallida / Rollback (`simular_error=True`) |
|:---|:---|:---|
| **Inicio** | `BEGIN` + `SELECT ... FOR UPDATE` sobre el material. | `BEGIN` + `SELECT ... FOR UPDATE` sobre el material. |
| **Insert de `OrdenDespacho`** | Se ejecuta y queda visible tras el commit. | Se ejecuta dentro de la transacción, pero se descarta. |
| **Insert de `DetalleDespacho`** | Se ejecuta y queda persistido. | Se ejecuta dentro de la transacción, pero se descarta. |
| **Update de stock** | `UPDATE ... SET stock = stock - n` confirmado. | `UPDATE` revertido; el stock vuelve al valor original. |
| **Excepción** | Ninguna. | `RuntimeError` lanzada tras las escrituras. |
| **Cierre** | `COMMIT` | `ROLLBACK` |
| **Estado final en BD** | Orden, detalle y stock descontado coherentes entre sí. | Sin orden, sin detalle y stock intacto: **ningún cambio parcial**. |
| **Propiedad ACID demostrada** | Atomicidad y Durabilidad. | Atomicidad y Consistencia. |

> **Nota:** SQLite no implementa `SELECT ... FOR UPDATE`; Django ignora `select_for_update()` en este motor sin lanzar error. Sin embargo, `transaction.atomic()` y `F()` sí funcionan, y el código queda listo para motores como PostgreSQL o MySQL, donde el bloqueo de fila sí se aplica.

---

## 📊 4. Panel Analítico y Consultas Agregadas en BD

En lugar de traer todos los registros a Python y sumar con bucles, los cálculos se delegan al motor SQL mediante `aggregate()` y `annotate()`.

| Operación ORM | Consulta SQL Equivalente | Propósito en el Dominio Logístico |
|:---|:---|:---|
| `Material.objects.aggregate(total=Sum('stock'))` | `SELECT SUM(stock) AS total FROM logistics_material;` | KPI de **unidades totales** en inventario. |
| `Material.objects.aggregate(valor=Sum(F('stock') * F('precio_unitario')))` | `SELECT SUM(stock * precio_unitario) AS valor FROM logistics_material;` | KPI de **valor monetario** del inventario. |
| `Material.objects.aggregate(prom=Avg('precio_unitario'), n=Count('id'))` | `SELECT AVG(precio_unitario), COUNT(id) FROM logistics_material;` | KPIs de **precio promedio** y **cantidad de referencias**. |
| `Categoria.objects.annotate(n_materiales=Count('materiales'))` | `SELECT c.*, COUNT(m.id) AS n_materiales FROM logistics_categoria c LEFT JOIN logistics_material m ON m.categoria_id = c.id GROUP BY c.id;` | Cuántos materiales tiene cada categoría. |
| `Material.objects.values('categoria__nombre').annotate(stock_total=Sum('stock'))` | `SELECT c.nombre, SUM(m.stock) AS stock_total FROM logistics_material m JOIN logistics_categoria c ON c.id = m.categoria_id GROUP BY c.nombre;` | **Stock consolidado por categoría** para decisiones de reabastecimiento. |
| `DetalleDespacho.objects.values('material__nombre').annotate(despachado=Sum('cantidad')).order_by('-despachado')` | `SELECT m.nombre, SUM(d.cantidad) AS despachado FROM logistics_detalledespacho d JOIN logistics_material m ON m.id = d.material_id GROUP BY m.nombre ORDER BY despachado DESC;` | **Ranking de materiales más despachados**. |

### Dashboard gerencial `/logistics/reporte/`

La vista `reporte_logistica_view` arma un panel de lectura para gerencia con:

- **Tarjetas KPI** en la parte superior: unidades totales, valor del inventario, precio promedio y número de referencias activas (resultado de `aggregate()`).
- **Tabla de stock por categoría:** agrupación con `values().annotate()`.
- **Tabla de ranking de despachos:** materiales ordenados por cantidad despachada.
- **Alertas de stock bajo:** listado generado con el QuerySet personalizado `stock_bajo()` (Sección 5).

---

## 🧩 5. QuerySets Semánticos Personalizados (`.as_manager()`)

Las reglas de negocio de lectura se encapsulan en un `QuerySet` propio, que luego se expone como *manager* del modelo.

```python
from django.db import models


class MaterialQuerySet(models.QuerySet):
    def con_stock(self):
        """Materiales con al menos una unidad disponible."""
        return self.filter(stock__gt=0)

    def stock_bajo(self, umbral=100):
        """Materiales cuyo stock está por debajo del umbral de reposición."""
        return self.filter(stock__lt=umbral)


class Material(models.Model):
    # ... campos definidos en la Sección 2 ...
    objects = MaterialQuerySet.as_manager()
```

Uso desde las vistas y el shell:

```python
Material.objects.con_stock()                      # Solo con existencias
Material.objects.stock_bajo()                     # Umbral por defecto: 100
Material.objects.stock_bajo(umbral=50)            # Umbral personalizado
Material.objects.con_stock().stock_bajo(30)       # Encadenamiento semántico
Material.objects.con_stock().select_related("categoria", "ficha")
```

**Ventajas de implementación:**

- **Encadenamiento semántico:** al heredar de `QuerySet`, los métodos se pueden combinar entre sí y con `filter()`, `order_by()`, `select_related()`, etc. El código se lee como una frase de negocio.
- **Principio DRY en controladores:** la regla "qué es stock bajo" vive en un solo lugar; si el criterio cambia, no hay que editar cada vista.
- **Compatibilidad con el CRUD estándar:** `.as_manager()` conserva `objects.all()`, `create()`, `get()`, el Django Admin y los formularios sin configuración adicional.
- **Testeabilidad:** los filtros de negocio se prueban de forma aislada, sin depender de las vistas.

---

## 🚀 6. Auditoría Empírica y Reducción del Problema N+1

El problema N+1 aparece cuando, tras una consulta principal, se dispara **una consulta adicional por cada objeto** al acceder a sus relaciones. Para medirlo se usa `connection.queries` en el shell (`python manage.py shell`):

```python
from django.db import connection, reset_queries
from django.conf import settings
from logistics.models import Material

settings.DEBUG = True  # connection.queries solo registra con DEBUG=True

# ---------- Escenario A: SIN optimizar ----------
reset_queries()
for m in Material.objects.all():
    _ = m.categoria.nombre      # 1:N -> 1 consulta extra por material
    _ = m.ficha.composicion     # 1:1 -> 1 consulta extra por material
print("Sin optimizar:", len(connection.queries), "consultas")

# ---------- Escenario B: CON select_related ----------
reset_queries()
for m in Material.objects.select_related("categoria", "ficha"):
    _ = m.categoria.nombre
    _ = m.ficha.composicion
print("Optimizado:", len(connection.queries), "consulta(s)")
```

### Resultados de la auditoría (N = 9 materiales)

| Escenario | Consultas SQL | Fórmula | Detalle |
|:---|:---:|:---:|:---|
| ❌ **Sin optimizar** | **19** | `1 + 2N` | 1 consulta base + 9 para `categoria` (1:N) + 9 para `ficha` (1:1). |
| ✅ **Optimizado con `select_related`** | **1** | `1` | Una única consulta con `INNER JOIN` a `logistics_categoria` y `logistics_fichatecnica`. |
| **Reducción** | **−18 consultas (≈ 94,7 %)** | — | El costo deja de crecer linealmente con el número de materiales. |

SQL generado por el escenario optimizado:

```sql
SELECT m.*, c.*, f.*
FROM logistics_material m
INNER JOIN logistics_categoria c ON m.categoria_id = c.id
INNER JOIN logistics_fichatecnica f ON f.material_id = m.id;
```

> El catálogo `/logistics/materiales/` ya implementa la versión optimizada, de modo que renderizar la lista no genera consultas adicionales por fila en el template.

---

## ⚖️ 7. Comparativa Arquitectónica: ORM Básico vs. ORM Avanzado

| Aspecto | ORM Básico (Lab 06) | ORM Avanzado (Lab 07) |
|:---|:---|:---|
| **Manejo de Stock** | `m.stock -= n; m.save()` en Python; vulnerable a *race conditions* (dos peticiones leen el mismo valor y una sobrescribe a la otra). | `update(stock=F('stock') - n)`: la resta se resuelve en SQL de forma atómica. |
| **Múltiples Escrituras** | Varios `save()` / `create()` independientes; un fallo intermedio deja datos huérfanos o inconsistentes. | `transaction.atomic()`: todo se confirma o todo se revierte (ACID). |
| **Lecturas Concurrentes** | Lectura sin bloqueo; el stock leído puede estar desactualizado al momento de escribir. | `select_for_update()` bloquea la fila durante la transacción (en motores que lo soportan). |
| **Métricas / Totales** | Bucles en Python sobre todos los objetos (`sum(m.stock for m in ...)`): alto consumo de memoria y red. | `aggregate()` / `annotate()`: el motor SQL calcula y devuelve solo el resultado. |
| **Filtros de Negocio** | `filter(stock__lt=100)` repetido y disperso en varias vistas. | `MaterialQuerySet` con `con_stock()` y `stock_bajo()`: lógica centralizada, encadenable y DRY. |
| **Carga de Relaciones** | Acceso perezoso (*lazy*): problema N+1 (`1 + 2N` consultas). | `select_related()`: una sola consulta con `JOIN`. |

---

## 💻 8. Puesta en Marcha Local y Endpoints Clave

### 8.1 Comandos (PowerShell)

```powershell
# 1. Clonar el repositorio
git clone https://github.com/Jesus-Rocha-B/Django_Lab06.git
cd Django_Lab06

# 2. Crear y activar el entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Aplicar migraciones
python manage.py makemigrations
python manage.py migrate

# 5. (Opcional) Crear superusuario para el panel de administración
python manage.py createsuperuser

# 6. Levantar el servidor de desarrollo
python manage.py runserver
```

### 8.2 Comandos equivalentes (Bash / Linux / macOS)

```bash
git clone https://github.com/Jesus-Rocha-B/Django_Lab06.git
cd Django_Lab06

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser   # opcional
python manage.py runserver
```

### 8.3 Enlaces locales de prueba

- **Despacho Transaccional con Rollback:** http://127.0.0.1:8000/logistics/despacho/transaccional/
- **Panel Analítico de Logística:** http://127.0.0.1:8000/logistics/reporte/
- **Catálogo Optimizado de Insumos:** http://127.0.0.1:8000/logistics/materiales/
- **Panel Comercial de Ventas:** http://127.0.0.1:8000/reportes/
- **Panel Administrativo Django:** http://127.0.0.1:8000/admin/
