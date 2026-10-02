from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.prenda_list, name='list'),
    # Lab 7 - Ejercicio 3: Alias de la lista para redirecciones del flujo de pedido
    path('', views.prenda_list, name='prenda_list'),

    path('nueva/', views.prenda_create, name='create'),
    path('<int:prenda_id>/', views.prenda_detail, name='detail'),
    
    # EJERCICIO 6: RUTAS DE CONSULTAS OPTIMIZADAS

    path('details/', views.prenda_detail_list, name='prenda_detail_list'),
    path('orders/', views.pedido_list, name='pedido_list'),

    # Lab 7 - Ejercicio 3: Ruta para registro transaccional de pedidos
    path('pedidos/transaccional/', views.pedido_transaccional_create, name='pedido_transaccional_create'),
]