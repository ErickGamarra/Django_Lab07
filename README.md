Laboratorio 07 — ORM Avanzado: Transacciones Atómicas, Agregaciones Analíticas, QuerySets Personalizados y Rendimiento SQL

Curso: Desarrollo de Aplicaciones Empresariales

Institución: Tecsup

Sección: 4 - C24 - Sección CD

Docente: Yunior Bestard Aroche

Integrantes del Equipo:

    Jesús Enrique Rocha Bobadilla

    Erick Arturo Gamarra Mundaca

    Proyecto: UrbanTrend — Plataforma Textil Streetwear y Sistema Logístico Avanzado con Django ORM y SQLite

    Repositorio GitHub: https://github.com/Jesus-Rocha-B/Django_Lab06.git

🎯 1. Objetivo del Laboratorio 07

Implementar patrones avanzados de persistencia, concurrencia, analítica delegada y optimización de rendimiento sobre el motor relacional de Django ORM en los dominios store (catálogo y checkout comercial) y logistics (cadena de suministro y abastecimiento de insumos textiles):

    Integridad Transaccional (ACID): Encapsular operaciones de múltiples escrituras en bloques indivisibles con transaction.atomic(), garantizando la reversión total (rollback) ante excepciones.

    Prevención de Condiciones de Carrera (Race Conditions): Delegar el descuento de existencias al motor de base de datos con expresiones F(), respaldado por bloqueo pesimista de filas (select_for_update()).

    Analítica de Alto Rendimiento en BD: Reemplazar el procesamiento algorítmico en memoria Python por funciones agregadas delegadas a SQL (aggregate(), annotate(), values().annotate()).

    Lógica de Dominio Centralizada (DRY): Desarrollar QuerySets personalizados con métodos semánticos encadenables asignados como managers mediante .as_manager().

    Eliminación del Problema de Consultas N+1: Auditar la saturación de I/O mediante connection.queries y aplicar carga anticipada (eager loading) con select_related() y prefetch_related().

🏗️ 2. Arquitectura de Módulos y Dominio Relacional

El sistema opera sobre una base de datos SQLite estructurada en dos dominios complementarios:
Plaintext

src/
├── core/templates/
│   └── base.html                          ◄── Layout maestro con Bootstrap 5.3
├── store/                                 ◄── DOMINIO COMERCIAL STREETWEAR
│   ├── models.py                          ◄── Prenda (PrendaQuerySet), Order, OrderItem
│   ├── views.py                           ◄── Checkout transaccional y reporte comercial
│   ├── urls.py                            ◄── Rutas de catálogo, compra y reportes
│   └── templates/store/
│       ├── checkout_transaccional.html    ◄── Formulario de compra con rollback
│       └── reporte_ventas.html            ◄── Panel analítico de facturación
└── logistics/                             ◄── DOMINIO LOGÍSTICO Y SUMINISTRO TEXTIL
    ├── models.py                          ◄── Material (MaterialQuerySet), OrdenDespacho, DetalleDespacho
    ├── forms.py                           ◄── RegistroDespachoForm (con simular_error)
    ├── views.py                           ◄── despacho_transaccional_view, reporte_logistics_view
    ├── urls.py                            ◄── Rutas /despacho/transaccional/, /reporte/, /materiales/
    └── templates/logistics/
        ├── despacho_form.html             ◄── Formulario con panel de auditoría en vivo
        ├── reporte.html                   ◄── Dashboard gerencial con tarjetas KPI y tablas
        └── material_list.html             ◄── Catálogo optimizado con select_related

Entidades y Relaciones Clave del Dominio Logístico

    Entidades Maestras: Proveedor, Sucursal y Transportista.

    Jerarquía 1:N con Cascada: CategoriaInsumo ➔ Material (stock, precio_unitario).

    Relación 1:1 Técnica: Material ➔ FichaTecnicaMaterial (especificaciones de composición y encogimiento).

    Relación N:M con Modelo Intermedio: OrdenDespacho vinculada a Material mediante DetalleDespacho, preservando atributos históricos: cantidad_despachada, costo_unitario_historico y lote_produccion.

⚡ 3. Control de Concurrencia y Transacciones Atómicas (ACID)

Se implementó el flujo transaccional de despacho de insumos en src/logistics/views.py (despacho_transaccional_view) integrando cuatro niveles de protección:
Python

with transaction.atomic():
    # 1. Bloqueo pesimista a nivel de fila (SELECT ... FOR UPDATE)
    material = Material.objects.select_for_update().get(pk=datos['material'].pk)
    
    if material.stock < cantidad:
        raise ValueError("Stock insuficiente.")

    # 2. Descuento atómico directo en SQL evitando condiciones de carrera
    stock_actualizado = Material.objects.filter(
        pk=material.pk,
        stock__gte=cantidad
    ).update(stock=F('stock') - cantidad)

    # 3. Escrituras multi-modelo dependientes
    despacho = OrdenDespacho.objects.create(...)
    DetalleDespacho.objects.create(
        despacho=despacho,
        material=material,
        cantidad_despachada=cantidad,
        costo_unitario_historico=material.precio_unitario
    )

    # 4. Interrupción inducida para auditar integridad
    if datos['simular_error']:
        raise Exception("Error forzado para comprobación de Rollback")

Escenario Evaluado	Acción Ejecutada	Resultado en Base de Datos
Transacción Exitosa (simular_error=False)	Despacho de 10 unidades de material.	COMMIT total: Se inserta OrdenDespacho, se crea DetalleDespacho y se descuenta el stock en Material.
Transacción Fallida (simular_error=True)	Excepción lanzada tras las escrituras.	ROLLBACK total: SQLite descarta todas las inserciones y el stock físico permanece intacto sin registros huérfanos.
📊 4. Panel Analítico y Consultas Agregadas en BD

Se sustituyó la agregación manual en memoria por consultas delegadas al motor relacional en reporte_logistics_view:
Operación ORM	Consulta SQL Equivalente	Propósito en el Dominio Logístico
DetalleDespacho.objects.aggregate()	SELECT SUM(cantidad), SUM(cantidad * costo), AVG(cantidad) FROM detalle_despacho	Calcula los KPIs globales del panel: total de insumos despachados, valorización monetaria histórica acumulada y promedio por despacho.
Material.objects.annotate()	SELECT material.*, SUM(detalle.cantidad) FROM material LEFT JOIN detalle GROUP BY material.id	Proyecta fila por fila la demanda acumulada y el número de despachos de cada insumo textil en el catálogo.
OrdenDespacho.objects.values().annotate()	SELECT estado, COUNT(id), SUM(detalle.subtotal) FROM orden GROUP BY estado	Agrupación gerencial que totaliza órdenes y montos monetarios consolidados según su estado logístico (En Tránsito, Entregado).

La plantilla logistics/reporte.html consume estos datos en tiempo real presentando 3 tarjetas métricas superiores y 2 tablas responsivas con Bootstrap 5.
🧩 5. QuerySets Semánticos Personalizados (.as_manager())

Se centralizaron las reglas de negocio de inventario implementando managers personalizados bajo el principio DRY:
Definición en src/logistics/models.py
Python

class MaterialQuerySet(models.QuerySet):
    def con_stock(self):
        """Filtra insumos con existencias físicas disponibles."""
        return self.filter(stock__gt=0)

    def stock_bajo(self, umbral=100):
        """Filtra insumos en nivel crítico de reposición."""
        return self.filter(stock__lte=umbral)

class Material(models.Model):
    objects = MaterialQuerySet.as_manager()
    # ... atributos del modelo

Ventajas de Implementación

    Encadenamiento directo: Permite consultas compuestas como Material.objects.con_stock().stock_bajo(200) generando una sola cláusula WHERE (stock > 0 AND stock <= 200).

    Reutilización en vistas: Utilizado en material_list para filtrar el catálogo público y en RegistroDespachoForm para impedir la selección de insumos sin existencias.

    Integridad del CRUD: Las operaciones estándar (create(), update(), delete()) en vistas y Django Admin continúan funcionando de forma transparente.

🚀 6. Auditoría Empírica y Reducción del Problema N+1

Se auditó en el shell de Django el impacto de consultar el catálogo de 9 materiales accediendo a su categoría (1:N) y a su ficha técnica textil (1:1):
Python

from django.db import connection, reset_queries
from logistics.models import Material

# Escenario Sin Optimizar (Lazy Loading)
reset_queries()
for m in list(Material.objects.all()):
    _ = m.categoria.nombre          # 1 consulta por cada FK
    _ = m.ficha_tecnica.composicion  # 1 consulta por cada OneToOne
consultas_sin_opt = len(connection.queries)

# Escenario Optimizado (Eager Loading)
reset_queries()
for m in list(Material.objects.select_related('categoria', 'ficha_tecnica').all()):
    _ = m.categoria.nombre
    _ = m.ficha_tecnica.composicion
consultas_con_opt = len(connection.queries)

Resultados de la Medición Empírica
Estrategia de Consulta	Sentencia ORM	Consultas SQL Ejecutadas	Comportamiento en Base de Datos
Sin Optimizar	Material.objects.all()	19 consultas (1+2N)	1 consulta inicial para materiales + 9 para categorías + 9 para fichas técnicas individuales.
Optimizado	Material.objects.select_related(...)	1 consulta	Un único LEFT OUTER JOIN / INNER JOIN que recupera todas las columnas relacionales de forma anticipada.
⚖️ 7. Comparativa Arquitectónica: ORM Básico vs. ORM Avanzado
Criterio Técnico	Implementación Convencional	Arquitectura Implementada (Lab 07)
Manejo de Stock	item.stock -= cant; item.save() propenso a sobreescrituras por concurrencia.	Expresión atómica F('stock') - cant ejecutada directamente en SQL.
Múltiples Escrituras	Sentencias aisladas sin control de fallos intermedios.	Bloque transaction.atomic() con reversión automática (ROLLBACK).
Lecturas Concurrentes	Lecturas sucias sin restricción de fila.	Bloqueo pesimista con select_for_update() a nivel de base de datos.
Métricas y Totales	Bucles for y sum() procesados en memoria RAM de Python.	Agregaciones directas en el RDBMS con aggregate() y annotate().
Filtros de Negocio	Métodos .filter() repetidos dispersos en controladores.	QuerySet personalizado con métodos semánticos encadenables vía .as_manager().
Carga de Relaciones	Lectura diferida (lazy loading) con latencia de red elevada (N+1).	Carga anticipada (eager loading) mediante select_related() y prefetch_related().
💻 8. Puesta en Marcha Local y Endpoints Clave
PowerShell

# 1. Clonar el repositorio
git clone https://github.com/Jesus-Rocha-B/Django_Lab06.git
cd Django_Lab06

# 2. Crear y activar el entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Aplicar migraciones y verificar integridad
cd src
python manage.py migrate

# 5. Iniciar servidor de desarrollo
python manage.py runserver

Puntos de Acceso Principales

    Despacho Transaccional con Rollback: http://127.0.0.1:8000/logistics/despacho/transaccional/

    Panel Analítico de Logística: http://127.0.0.1:8000/logistics/reporte/

    Catálogo Optimizado de Insumos: http://127.0.0.1:8000/logistics/materiales/

    Panel Comercial de Ventas: http://127.0.0.1:8000/reportes/

    Panel Administrativo Django: http://127.0.0.1:8000/admin/
