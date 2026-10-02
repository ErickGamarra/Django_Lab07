import uuid

from django.contrib import messages
from django.db import transaction

from django.db.models import Avg, Count, DecimalField, F, Q, Sum
from django.shortcuts import render, redirect
from django.http import Http404
from django.db import connection, reset_queries
from .models import DetallePedido, Pedido, Prenda, ResenaPrenda
from .forms import PrendaForm, RegistroPedidoForm, ResenaPrendaForm


def prenda_list(request):
    query = request.GET.get('q', '').strip().lower()
    tipo = request.GET.get('tipo', '').strip()
    categoria = request.GET.get('categoria', '').strip()

    prendas = Prenda.objects.filter(activo=True)

    if query:
        prendas = prendas.filter(
            Q(nombre__icontains=query) |
            Q(marca__icontains=query) |
            Q(descripcion__icontains=query)
        )

    if tipo:
        prendas = prendas.filter(tipo=tipo)

    if categoria:
        prendas = prendas.filter(categoria=categoria)

    total_catalogo = Prenda.objects.filter(activo=True).count()
    total_stock_global = sum(p.stock for p in Prenda.objects.filter(activo=True))
    total_activas = Prenda.objects.filter(activo=True, disponible=True).count()

    contexto = {
        'titulo': 'Catálogo de Ropa Streetwear',
        'prendas': prendas,
        'query': request.GET.get('q', ''),
        'tipo_seleccionado': tipo,
        'categoria_seleccionada': categoria,
        'total_resultados': prendas.count(),
        'total_catalogo': total_catalogo,
        'total_stock_global': total_stock_global,
        'total_activas': total_activas,
    }
    return render(request, 'store/prenda_list.html', contexto)


def prenda_detail(request, prenda_id):
    try:
        prenda = Prenda.objects.get(id=prenda_id, activo=True)
    except Prenda.DoesNotExist:
        raise Http404(f"La prenda con ID #{prenda_id} no existe o no está activa.")

    resena_form = ResenaPrendaForm()

    if request.method == 'POST' and 'submit_resena' in request.POST:
        resena_form = ResenaPrendaForm(request.POST)
        if resena_form.is_valid():
            ResenaPrenda.objects.create(
                prenda=prenda,
                cliente_nombre=resena_form.cleaned_data['cliente_nombre'],
                calificacion=int(resena_form.cleaned_data['calificacion']),
                comentario=resena_form.cleaned_data['comentario'],
            )
            return redirect('store:detail', prenda_id=prenda.id)

    resenas = prenda.resenas.all()
    total_resenas = resenas.count()
    promedio_calificacion = round(sum(r.calificacion for r in resenas) / total_resenas, 1) if total_resenas > 0 else None

    return render(request, 'store/prenda_detail.html', {
        'prenda': prenda,
        'titulo': f"Detalle: {prenda.nombre}",
        'resenas': resenas,
        'total_resenas': total_resenas,
        'promedio_calificacion': promedio_calificacion,
        'resena_form': resena_form,
    })


def prenda_create(request):
    if request.method == 'POST':
        form = PrendaForm(request.POST)
        if form.is_valid():
            Prenda.objects.create(
                nombre=form.cleaned_data['nombre'],
                marca=form.cleaned_data['marca'],
                tipo=form.cleaned_data['tipo'],
                categoria=form.cleaned_data['categoria'],
                talla=form.cleaned_data['talla'],
                precio=form.cleaned_data['precio'],
                stock=form.cleaned_data['stock'],
                disponible=form.cleaned_data['disponible'],
                activo=form.cleaned_data.get('activo', True),
                descripcion=form.cleaned_data['descripcion'],
            )
            return redirect('store:list')
    else:
        form = PrendaForm()

    return render(request, 'store/prenda_form.html', {
        'titulo': 'Registrar Nueva Prenda',
        'form': form,
    })


# EJERCICIO 6: CONSULTAS DE RELACIONES OPTIMIZADAS


def prenda_detail_list(request):
    """
    1:1 relationship optimized via select_related.
    Retrieves active garments with their technical sheet (DetallePrenda)
    in a single SQL query (JOIN).
    """
    reset_queries()

    prendas = Prenda.objects.filter(activo=True).select_related('detalle')

    lista_prendas = list(prendas)
    total_consultas = len(connection.queries)

    return render(request, 'store/prenda_detail_list.html', {
        'titulo': 'Catálogo con Ficha Técnica (select_related)',
        'prendas': lista_prendas,
        # La plantilla espera este nombre para mostrar el contador SQL.
        'total_consultas': total_consultas,
    })


def pedido_list(request):
    """
    N:M intermediate relationship optimized via prefetch_related.
    Retrieves orders, intermediate order details, and related garments
    executing separate queries and caching them in memory.
    """
    reset_queries()

    pedidos = Pedido.objects.prefetch_related('detalles__prenda')

    lista_pedidos = list(pedidos)
    total_consultas = len(connection.queries)

    return render(request, 'store/pedido_list.html', {
        'titulo': 'Listado de Pedidos y Detalles (prefetch_related)',
        'pedidos': lista_pedidos,
        # La plantilla espera este nombre para mostrar el contador SQL.
        'total_consultas': total_consultas,
    })


# Lab 7 - Ejercicio 3: Vista transaccional con atomicidad y F()
def pedido_transaccional_create(request):
    if request.method == 'POST':
        form = RegistroPedidoForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            cantidad = datos['cantidad']

            try:
                # Lab 7 - Ejercicio 3: Inicio de transacción atómica
                with transaction.atomic():
                    prenda = Prenda.objects.select_for_update().get(
                        pk=datos['prenda'].pk,
                        activo=True,
                    )
                    if prenda.stock < cantidad:
                        raise ValueError(
                            f"Stock insuficiente: hay {prenda.stock} unidades de "
                            f"{prenda.nombre} y se solicitaron {cantidad}."
                        )

                    # Lab 7 - Ejercicio 3: Descuento atómico de stock con expresión F()
                    Prenda.objects.filter(pk=prenda.pk).update(
                        stock=F('stock') - cantidad
                    )

                    codigo = f"PED-{uuid.uuid4().hex[:6].upper()}"
                    while Pedido.objects.filter(codigo=codigo).exists():
                        codigo = f"PED-{uuid.uuid4().hex[:6].upper()}"

                    pedido = Pedido.objects.create(
                        codigo=codigo,
                        cliente_nombre=datos['cliente_nombre'],
                        cliente_email=datos['cliente_email'],
                        estado='Pagado',
                    )
                    DetallePedido.objects.create(
                        pedido=pedido,
                        prenda=prenda,
                        cantidad=cantidad,
                        precio_unitario=prenda.precio,
                    )
            except Exception as e:
                messages.error(request, f"No se pudo registrar el pedido: {e}")
            else:
                messages.success(
                    request,
                    f"Pedido {pedido.codigo} registrado y pagado correctamente.",
                )
                return redirect('store:prenda_list')
    else:
        form = RegistroPedidoForm()

    return render(request, 'store/pedido_transaccional_form.html', {
        'titulo': 'Registrar pedido transaccional',
        'form': form,
    })


# Lab 7 - Ejercicio 6: Vista de reporte analítico con agregaciones y anotaciones
def reporte_store_view(request):
    # Lab 7 - Ejercicio 6: Métricas globales de prendas, ventas y satisfacción
    metricas_prendas = Prenda.objects.filter(activo=True).aggregate(
        total_prendas=Count('id'),
        stock_total=Sum('stock'),
        precio_promedio=Avg('precio'),
    )
    facturacion = DetallePedido.objects.aggregate(
        facturacion_total=Sum(F('cantidad') * F('precio_unitario')),
    )
    satisfaccion = ResenaPrenda.objects.aggregate(
        satisfaccion_promedio=Avg('calificacion'),
    )

    # Lab 7 - Ejercicio 6: Agrupación de pedidos por estado y facturación
    pedidos_por_estado = Pedido.objects.values('estado').annotate(
        cantidad=Count('id', distinct=True),
        total=Sum(
            F('detalles__cantidad') * F('detalles__precio_unitario'),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    ).order_by('-cantidad')

    # Lab 7 - Ejercicio 6: Métricas por prenda mediante anotaciones ORM
    prendas_metricas = Prenda.objects.filter(activo=True).annotate(
        num_resenas=Count('resenas', distinct=True),
        calificacion_prom=Avg('resenas__calificacion'),
        num_pedidos=Count('detalles_pedido', distinct=True),
    ).order_by('-num_resenas')[:10]

    # Lab 7 - Ejercicio 6: Contexto del dashboard analítico
    contexto = {
        'titulo': 'Reporte Analítico de la Tienda',
        'total_prendas': metricas_prendas['total_prendas'],
        'stock_total': metricas_prendas['stock_total'],
        'precio_promedio': metricas_prendas['precio_promedio'],
        'facturacion_total': facturacion['facturacion_total'],
        'satisfaccion_promedio': satisfaccion['satisfaccion_promedio'],
        'pedidos_por_estado': pedidos_por_estado,
        'prendas_metricas': prendas_metricas,
    }
    return render(request, 'store/reporte.html', contexto)