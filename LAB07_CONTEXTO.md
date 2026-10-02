# Contexto de Proyecto: UrbanTrend — Laboratorio 07 (ORM Avanzado)

## 1. Arquitectura y Stack Tecnológico
- **Framework:** Django 5.x / 6.x (Patrón MVT).
- **Base de Datos:** SQLite (`src/db.sqlite3`).
- **Frontend:** Bootstrap 5.3.3 + Django Template Language (DTL).
- **Estructura Modular:**
  - `src/core/`: Plantilla maestra (`core/templates/base.html`).
  - `src/store/`: Dominio comercial de prendas, reseñas y pedidos.
  - `src/logistics/`: Dominio industrial de insumos textiles, proveedores y despachos.

## 2. Estado Actual y Antecedentes (Completado)
- **Lab 04 (Persistencia Relacional Avanzada):**
  - Modelos 1:1 (`DetallePrenda`, `FichaTecnicaMaterial`).
  - Modelos 1:N (`ResenaPrenda`, `Material.categoria`).
  - Modelos N:M con tabla intermedia `through`:
    - `Pedido` ↔ `Prenda` vía `DetallePedido` (atributos: `cantidad`, `precio_unitario`).
    - `OrdenDespacho` ↔ `Material` vía `DetalleDespacho` (atributos: `cantidad_despachada`, `costo_unitario_historico`, `lote_produccion`).
  - Señales `post_save` para creación automática de fichas 1:1.
  - Integridad con `models.PROTECT` en categorías logísticas.
- **Lab 05 (Django Admin Backoffice):**
  - `ModelAdmin` con `StackedInline` (1:1) y `TabularInline` (N:M intermedios).
  - Manejo de colisión de señales en `save_formset`.
- **Lab 06 (Capa Visual DTL & DRY):**
  - Herencia global desde `base.html`.
  - Componentes modulares en subcarpetas `includes/`.
  - Filtros DTL estándar (`|upper`, `|floatformat:2`, `|date`, `|pluralize`).
- **Lab 07 — Estado Actual:**
  - **Ejercicio 1:** Completado. Identificados `Prenda.stock`, `Pedido.estado`, `DetallePedido.cantidad`/`precio_unitario`. Esquema físico de base de datos intacto.
  - **Ejercicio 2:** Completado. Base de datos sembrada con datos de prueba suficientes (>=5 prendas, >=3 reseñas, >=8 detalles).

## 3. Hoja de Ruta Pendiente — Laboratorio 07

### PARTE 1: Dominio Comercial (`store`)
- **Ejercicio 3 (Transacción Atómica y Concurrencia):**
  - Crear Formulario (`RegistroPedidoForm`), Vista (`pedido_transaccional_create`), URL y Template (`pedido_transaccional_form.html` extends `base.html`).
  - Lógica: `with transaction.atomic():`, validar stock, descontar usando `F('stock') - cantidad`, crear `Pedido` y `DetallePedido`.
  - Manejo de excepción con rollback completo si falta stock. Patrón Post/Redirect/Get.
- **Ejercicio 4 (Cálculo Global con `aggregate()`):**
  - Query para shell: Facturación histórica total con `Sum(F('cantidad') * F('precio_unitario'))`.
- **Ejercicio 5 (Analítica por Objeto y Agrupación con `annotate()`):**
  - Query para shell: Cantidad de reseñas/pedidos por prenda (`Count`).
  - Query para shell: Pedidos agrupados por estado con `values('estado').annotate(total=Count('id'))`.
- **Ejercicio 6 (Página de Reporte):**
  - Vista `reporte_store_view`, URL `/ropa/reporte/` y Template `reporte.html` (extends `base.html`, Bootstrap cards/tablas, filtros `|floatformat:2`).
- **Ejercicio 7 (QuerySet Personalizado):**
  - Crear `PrendaQuerySet(models.QuerySet)` con métodos encadenables (`disponibles()`, `stock_critico()`, etc.).
  - Asignar en modelo con `objects = PrendaQuerySet.as_manager()`.
  - Refactorizar al menos 2 vistas en `store/views.py`.
- **Ejercicio 8 (Medición Empírica $N+1$):**
  - Medir `len(connection.queries)` sin optimizar vs con `select_related('detalle')` o `prefetch_related('detalles__prenda')`.

### PARTE 2: Dominio Logístico (`logistics`)
- **Ejercicios 9 al 13:**
  - Replicar exactamente la misma metodología sobre `logistics`:
    - Transacción en despacho descontando `Material.stock` con `F()`.
    - Reporte `logistics` con `aggregate()` y `annotate()`.
    - `MaterialQuerySet` personalizado con `as_manager()`.
    - Medición de consultas en órdenes de despacho.
- **Ejercicio 14:**
  - Actualización de `requirements.txt`, `README.md` y push final a GitHub.

## 4. Reglas Estrictas de Implementación
1. NO crear entidades o tablas nuevas. Trabajar sobre las existentes.
2. Todo template nuevo DEBE heredar de `core/templates/base.html`.
3. Mantener tipado y convenciones de nombres existentes en `src/store/` y `src/logistics/`.
4. El código debe ser modular, documentado y cumplir estrictamente el principio DRY.