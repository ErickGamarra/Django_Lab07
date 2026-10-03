from django.urls import path
from . import views

app_name = 'logistics'

urlpatterns = [
    # Dashboard principal de logistica
    path('', views.index_logistics, name='index'),

    # Lab 7 - Parte 2 (Criterio 5): Ruta del panel analítico de logística
    path('reporte/', views.reporte_logistics_view, name='reporte_logistics'),

    # CRUD: Materiales (1:N y 1:1)
    path('materiales/', views.material_list, name='material_list'),
    path('materiales/nuevo/', views.material_create, name='material_create'),
    path('materiales/<int:pk>/', views.material_detail, name='material_detail'),
    path('materiales/editar/<int:pk>/', views.material_update, name='material_update'),
    path('materiales/eliminar/<int:pk>/', views.material_delete, name='material_delete'),

    # Relación 1:1 — Ficha Técnica Textil
    path('fichas-tecnicas/editar/<int:pk>/', views.ficha_tecnica_update, name='ficha_tecnica_update'),

    # Cabecera N:M — Órdenes de Despacho
    path('despachos/', views.orden_despacho_list, name='orden_despacho_list'),
    path('despachos/nuevo/', views.orden_despacho_create, name='orden_despacho_create'),
    # Lab 7 - Parte 2 (Criterios 1 y 2): Ruta del formulario de despacho transaccional
    path('despacho/transaccional/', views.despacho_transaccional_view, name='despacho_transaccional'),
    path('despachos/<int:pk>/', views.orden_despacho_detail, name='orden_despacho_detail'),
    path('despachos/editar/<int:pk>/', views.orden_despacho_update, name='orden_despacho_update'),
    path('despachos/eliminar/<int:pk>/', views.orden_despacho_delete, name='orden_despacho_delete'),

    # CRUD Modelo Intermedio — Detalle Despacho (Criterio 9)
    path('detalles-despacho/', views.detalle_despacho_list, name='detalle_despacho_list'),
    path('detalles-despacho/nuevo/', views.detalle_despacho_create, name='detalle_despacho_create'),
    path('detalles-despacho/nuevo/<int:despacho_id>/', views.detalle_despacho_create, name='detalle_despacho_create_for_despacho'),
    path('detalles-despacho/editar/<int:pk>/', views.detalle_despacho_update, name='detalle_despacho_update'),
    path('detalles-despacho/eliminar/<int:pk>/', views.detalle_despacho_delete, name='detalle_despacho_delete'),

    # CRUD: Categorías (Entidad Maestra 1:N)
    path('categorias/', views.categoria_list, name='categoria_list'),
    path('categorias/nuevo/', views.categoria_create, name='categoria_create'),
    path('categorias/eliminar/<int:pk>/', views.categoria_delete, name='categoria_delete'),

    # CRUD: Proveedores (Entidad Independiente)
    path('proveedores/', views.proveedor_list, name='proveedor_list'),
    path('proveedores/nuevo/', views.proveedor_create, name='proveedor_create'),
]

