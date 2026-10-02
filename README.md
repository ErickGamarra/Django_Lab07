# Laboratorio 06 — Herencia, Filtros y Reutilización de Templates con Django Template Language (DTL)

**Curso:** Desarrollo de Aplicaciones Empresariales  
**Institución:** Tecsup  
**Sección:** 4 - C24 - Sección CD  
**Docente:** Yunior Bestard Aroche  
**Integrantes del Equipo:**
1. **Jesús Enrique Rocha Bobadilla**
2. **Erick Arturo Gamarra Mundaca**  
**Proyecto:** **UrbanTrend** — Plataforma Textil Streetwear y Sistema Logístico Avanzado con Django ORM y SQLite  
**Repositorio GitHub:** [https://github.com/Jesus-Rocha-B/Django_Lab06.git](https://github.com/Jesus-Rocha-B/Django_Lab06.git)

---

## 🎯 1. Objetivo del Laboratorio 06

Refactorizar y optimizar la capa de presentación visual de las aplicaciones **`store`** (catálogo streetwear) y **`logistics`** (gestión de abastecimiento e insumos) mediante las mejores prácticas del **Django Template Language (DTL)**:
* **Herencia de plantillas (`{% extends %}` y `{% block %}`):** Centralizar la estructura HTML5, estilos responsivos con Bootstrap 5.3 y elementos comunes en una plantilla maestra ([`base.html`](file:///d:/Django/Lab06/Django_Lab06/src/core/templates/base.html)), eliminando duplicidad.
* **Transformación y formato con filtros de Django:** Aplicar filtros estándar como `|upper`, `|floatformat:2`, `|date` y `|pluralize` para estandarizar la presentación de datos numéricos y cadenas.
* **Modularidad y principio DRY con `{% include %}`:** Extraer componentes visuales repetitivos a fragmentos reutilizables en subcarpetas `includes/`.
* **Documentación técnica de servidor (`{# ... #}`):** Documentar la lógica condicional compleja de las plantillas sin exponer notas internas en el DOM del cliente.
* **Seguridad y mitigación de XSS:** Validar el sistema de auto-escape nativo de Django ante entradas con caracteres maliciosos (`<script>`).

---

## 🏗️ 2. Arquitectura de Plantillas y Herencia

Todas las pantallas de la solución heredan de [`core/templates/base.html`](file:///d:/Django/Lab06/Django_Lab06/src/core/templates/base.html), la cual establece:
1. Cabecera HTML5, metadatos y fuentes tipográficas Google Fonts (*Inter*).
2. Estilos globales con CDN de **Bootstrap 5.3.3** e iconos **Bootstrap Icons 1.11.3**.
3. Barra de navegación principal (*Navbar*) con enlaces directos al catálogo y al menú desplegable logístico.
4. Contenedor principal con soporte de mensajes flash (`django.contrib.messages`) y bloque extensible `{% block content %}`.
5. Pie de página unificado y carga de scripts al cierre del `<body>`.

```text
src/
├── core/templates/
│   └── base.html                          ◄── PLANTILLA PADRE (Layout Maestro)
├── store/templates/store/
│   ├── prenda_list.html                   ◄── HEREDA de base.html (Catálogo)
│   ├── prenda_detail.html                 ◄── HEREDA de base.html (Detalle Prenda)
│   ├── prenda_form.html                   ◄── HEREDA de base.html (Formulario Prenda)
│   └── includes/
│       └── badge_disponibilidad.html      ◄── COMPONENTE REUTILIZABLE (Include)
└── logistics/templates/logistics/
    ├── material_list.html                 ◄── HEREDA de base.html (Listado Insumos)
    ├── orden_despacho_list.html           ◄── HEREDA de base.html (Listado Despachos)
    ├── orden_despacho_detail.html         ◄── HEREDA de base.html (Detalle N:M)
    ├── detalle_despacho_list.html         ◄── HEREDA de base.html (CRUD Intermedio)
    └── includes/
        ├── badge_estado_despacho.html     ◄── COMPONENTE REUTILIZABLE (Include)
        └── detalle_despacho_row.html      ◄── COMPONENTE REUTILIZABLE N:M (Include)
```

---

## 🧩 3. Componentes Reutilizables Extraídos con `{% include %}`

Se crearon e implementaron componentes modulares para cumplir el principio **DRY (Don't Repeat Yourself)**:

| Componente | Archivo Creado | Templates donde se reutiliza | Qué resuelve |
| :--- | :--- | :--- | :--- |
| **Badge de Disponibilidad** | `store/includes/badge_disponibilidad.html` | [`prenda_list.html`](file:///d:/Django/Lab06/Django_Lab06/src/store/templates/store/prenda_list.html), [`prenda_detail.html`](file:///d:/Django/Lab06/Django_Lab06/src/store/templates/store/prenda_detail.html) | Estandariza la insignia comercial que indica si una prenda está disponible o agotada según su stock. |
| **Insignia Estado de Despacho** | `logistics/includes/badge_estado_despacho.html` | [`orden_despacho_list.html`](file:///d:/Django/Lab06/Django_Lab06/src/logistics/templates/logistics/orden_despacho_list.html), [`orden_despacho_detail.html`](file:///d:/Django/Lab06/Django_Lab06/src/logistics/templates/logistics/orden_despacho_detail.html) | Conmuta colores contextuales de Bootstrap según el estado de la guía (`Borrador`, `En Tránsito`, `Entregado`, `Cancelado`). |
| **Fila Modelo Intermedio N:M** | `logistics/includes/detalle_despacho_row.html` | [`orden_despacho_detail.html`](file:///d:/Django/Lab06/Django_Lab06/src/logistics/templates/logistics/orden_despacho_detail.html), [`detalle_despacho_list.html`](file:///d:/Django/Lab06/Django_Lab06/src/logistics/templates/logistics/detalle_despacho_list.html) | Renderiza de manera homogénea las instancias intermedias de `DetalleDespacho` con sus atributos propios (lote, cantidad, costo unitario histórico, subtotal y botones de acción CRUD). |

---

## 🎨 4. Aplicación de Filtros de Django (DTL)

Se incorporaron filtros sobre campos ya existentes para enriquecer la presentación visual sin alterar la base de datos:

1. **`|upper` (Mayúsculas sostenidas):**
   * `{{ prenda.nombre|upper }}` en [`prenda_list.html`](file:///d:/Django/Lab06/Django_Lab06/src/store/templates/store/prenda_list.html).
   * `{{ m.nombre|upper }}` en [`material_list.html`](file:///d:/Django/Lab06/Django_Lab06/src/logistics/templates/logistics/material_list.html).
2. **`|floatformat:2` (Formateo monetario):**
   * `S/ {{ prenda.precio|floatformat:2 }}` en el catálogo de prendas.
   * `S/ {{ m.precio_unitario|floatformat:2 }}` en el costo unitario de insumos textiles.
   * `S/ {{ d.subtotal|floatformat:2 }}` en los ítems despachados.
3. **`|date` (Formateo de fechas):**
   * `{{ d.fecha_emision|date:"d/m/Y H:i" }}` en las guías de remisión y órdenes logísticas.
4. **`|pluralize` y `|length` (Concordancia gramatical):**
   * `{{ total_resultados }} prenda{{ total_resultados|pluralize:"s" }}` adaptando automáticamente singular o plural.

---

## 📝 5. Documentación con Comentarios de Servidor `{# #}`

Se añadieron comentarios con sintaxis `{# ... #}` en secciones clave de las plantillas:
* Explicación de la asignación condicional de distintivos por segmento de público (`Hombre`, `Mujer`, `Niños`, `Unisex`).
* Documentación de la comprobación de inventario crítico para alternar entre el badge de *Agotado* y las unidades físicas.
* Documentación del recorrido de relaciones ORM **1:N** (Material ➔ Categoría) y **1:1** (Material ➔ Ficha Técnica).
* **Diferencia clave con comentarios HTML:** A diferencia de `<!-- -->`, los comentarios con `{# #}` son eliminados por Django en el servidor y **nunca llegan al código fuente del navegador**.

---

## 🛡️ 6. Verificación de Seguridad y Auto-Escape XSS

Se realizó una prueba de inyección de código mediante el ingreso de:
```html
<script>alert("XSS")</script>
```
* **Comportamiento en la interfaz:** El navegador lo presenta como texto plano literal `<SCRIPT>ALERT("XSS")</SCRIPT>` sin ejecutar el script.
* **Comprobación en el código feoeuente (`Ctrl + U`):**
  ```html
  <span class="fw-bold text-dark d-block mb-0">&lt;SCRIPT&gt;ALERT(&quot;XSS&quot;)&lt;/SCRIPT&gt;</span>
  ```
* **Conclusión:** Django escapa por defecto los caracteres peligrosos (`<` a `&lt;`, `>` a `&gt;`, `"` a `&quot;`), neutralizando los ataques de **Cross-Site Scripting**.

---

## ⚖️ 7. Comparativa: Templates Refactorizados vs. Django Admin

| Criterio | Django Admin (Semana 5) | Aplicación Refactorizada (Semana 6) |
| :--- | :--- | :--- |
| **Audiencia** | Uso interno exclusivo para administradores técnicos (`is_staff`). | Interfaz pública y amigable orientada a clientes y operarios de almacén. |
| **Diseño y UX** | Monocromático, rígido y tabular. | Moderno con **Bootstrap 5**, micro-interacciones, diseño responsivo y KPIs en tiempo real. |
| **Relaciones Complejas** | Formularios planos o inlines tabulares difíciles de auditar. | Fichas consolidadas con tarjetas de resumen financiero, atributos del modelo intermedio N:M anidados y navegación visual. |
| **Mantenibilidad (DRY)** | Sobreescritura compleja de plantillas internas de Django. | **Modularidad pura**: modificación centralizada de componentes reutilizables mediante `{% include %}`. |
| **Seguridad** | Expone la estructura de tablas y metadatos del sistema. | **Principio de menor privilegio**: URLs públicas desacopladas (`/ropa/`, `/logistics/`) sin acceso al panel administrativo. |

---

## 🚀 8. Puesta en Marcha Local

```powershell
# 1. Clonar el repositorio
git clone https://github.com/Jesus-Rocha-B/Django_Lab06.git
cd Django_Lab06

# 2. Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Aplicar migraciones SQLite y sembrar datos de prueba
cd src
python manage.py migrate
python seed_prendas.py
python seed_logistics.py

# 5. Iniciar servidor de desarrollo
python manage.py runserver
```

* **Catálogo de Prendas (App Store):** [http://127.0.0.1:8000/ropa/](http://127.0.0.1:8000/ropa/)
* **Módulo de Logística (App Logistics):** [http://127.0.0.1:8000/logistics/](http://127.0.0.1:8000/logistics/)
* **Listado de Insumos Textiles:** [http://127.0.0.1:8000/logistics/materiales/](http://127.0.0.1:8000/logistics/materiales/)
* **Detalle de Orden de Despacho (N:M):** [http://127.0.0.1:8000/logistics/despachos/1/](http://127.0.0.1:8000/logistics/despachos/1/)
* **CRUD de Modelo Intermedio:** [http://127.0.0.1:8000/logistics/detalles-despacho/](http://127.0.0.1:8000/logistics/detalles-despacho/)
* **Panel Administrativo:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
