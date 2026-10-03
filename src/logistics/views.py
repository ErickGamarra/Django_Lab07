import uuid

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Avg, Count, DecimalField, F, Sum
from django.db.models import ProtectedError
from .models import (
    Proveedor,
    Sucursal,
    Transportista,
    CategoriaInsumo,
    Material,
    FichaTecnicaMaterial,
    OrdenDespacho,
    DetalleDespacho,
)
from .forms import (
    ProveedorForm,
    SucursalForm,
    TransportistaForm,
    CategoriaInsumoForm,
    MaterialForm,
    FichaTecnicaMaterialForm,
    OrdenDespachoForm,
    DetalleDespachoForm,
    RegistroDespachoForm,
)


# ============================================================
# PANEL PRINCIPAL (DASHBOARD)
# ============================================================

def index_logistics(request):
    contexto = {
        'total_proveedores': Proveedor.objects.count(),
        'total_sucursales': Sucursal.objects.count(),
        'total_transportistas': Transportista.objects.filter(activo=True).count(),
        'total_categorias': CategoriaInsumo.objects.count(),
        'total_materiales': Material.objects.count(),
        'total_despachos': OrdenDespacho.objects.count(),
        'total_detalles_despacho': DetalleDespacho.objects.count(),
        'materiales_recientes': Material.objects.select_related('categoria', 'ficha_tecnica').all()[:5],
        'despachos_recientes': OrdenDespacho.objects.select_related('sucursal_destino', 'transportista').all()[:5],
    }
    return render(request, 'logistics/index.html', contexto)


# Lab 7 - Parte 2 (Criterio 5): Vista del panel analítico de logística
def reporte_logistics_view(request):
    # Lab 7 - Parte 2 (Criterio 5): Agregar unidades, valorización y promedio por línea
    metricas_globales = DetalleDespacho.objects.aggregate(
        total_unidades=Sum('cantidad_despachada'),
        costo_total=Sum(
            F('cantidad_despachada') * F('costo_unitario_historico'),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        promedio_por_linea=Avg(
            F('cantidad_despachada') * F('costo_unitario_historico'),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    )

    # Lab 7 - Parte 2 (Criterio 5): Anotar la demanda acumulada y cantidad de despachos por material
    # Lab 7 - Parte 2 (Criterio 7): Usar con_stock() para el reporte de demanda de materiales disponibles
    consumo_por_material = Material.objects.con_stock().annotate(
        total_despachado=Sum('detalles_despacho__cantidad_despachada'),
        total_pedidos=Count('detalles_despacho', distinct=True),
    ).select_related('categoria').order_by('-total_despachado')

    # Lab 7 - Parte 2 (Criterio 5): Agrupar órdenes por estado y calcular unidades y valor despachado
    despachos_por_estado = OrdenDespacho.objects.values('estado').annotate(
        total_ordenes=Count('id', distinct=True),
        total_unidades=Sum('detalles__cantidad_despachada'),
        valor_total=Sum(
            F('detalles__cantidad_despachada') * F('detalles__costo_unitario_historico'),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    ).order_by('-total_ordenes')

    # Lab 7 - Parte 2 (Criterio 5): Entregar métricas y reportes analíticos a la plantilla
    contexto = {
        'titulo': 'Panel Analítico de Logística',
        **metricas_globales,
        'consumo_por_material': consumo_por_material,
        'despachos_por_estado': despachos_por_estado,
    }
    return render(request, 'logistics/reporte.html', contexto)


# ============================================================
# CRUD: MATERIALES (OPTIMIZADO CON 1:N Y 1:1 VÍA select_related)
# ============================================================

def material_list(request):
    # Lab 7 - Parte 2 (Criterio 7): Usar con_stock() para mostrar materiales disponibles en el catálogo
    materiales = Material.objects.con_stock().select_related('categoria', 'ficha_tecnica')
    return render(request, 'logistics/material_list.html', {'materiales': materiales})


def material_detail(request, pk):
    material = get_object_or_404(
        Material.objects.select_related('categoria', 'ficha_tecnica'),
        pk=pk
    )
    # Obtener historial de despachos donde se utilizó este material (recorrido inverso del modelo intermedio)
    despachos_asociados = material.detalles_despacho.select_related('despacho', 'despacho__sucursal_destino').all()
    return render(request, 'logistics/material_detail.html', {
        'material': material,
        'despachos_asociados': despachos_asociados
    })


def material_create(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save()
            # La señal post_save crea automáticamente la FichaTecnicaMaterial
            messages.success(request, f'Material "{material.nombre}" registrado exitosamente con su Ficha Técnica textil.')
            return redirect('logistics:material_list')
    else:
        form = MaterialForm()
    return render(request, 'logistics/material_form.html', {'form': form, 'titulo': 'Registrar Insumo / Material'})


def material_update(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, f'Material "{material.nombre}" actualizado correctamente.')
            return redirect('logistics:material_list')
    else:
        form = MaterialForm(instance=material)
    return render(request, 'logistics/material_form.html', {'form': form, 'titulo': 'Editar Insumo / Material'})


def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        try:
            material.delete()
            messages.warning(request, f'El material "{material.nombre}" fue eliminado del catálogo.')
            return redirect('logistics:material_list')
        except ProtectedError:
            messages.error(
                request,
                f'No se puede eliminar "{material.nombre}" porque está asignado a órdenes de despacho activas.'
            )
            return redirect('logistics:material_list')
    return render(request, 'logistics/material_confirm_delete.html', {'objeto': material})


# ============================================================
# GESTIÓN DE RELACIÓN 1:1 — FICHA TÉCNICA
# ============================================================

def ficha_tecnica_update(request, pk):
    ficha = get_object_or_404(FichaTecnicaMaterial.objects.select_related('material'), pk=pk)
    if request.method == 'POST':
        form = FichaTecnicaMaterialForm(request.POST, instance=ficha)
        if form.is_valid():
            form.save()
            messages.success(request, f'Ficha Técnica de "{ficha.material.nombre}" actualizada correctamente.')
            return redirect('logistics:material_detail', pk=ficha.material.pk)
    else:
        form = FichaTecnicaMaterialForm(instance=ficha)
    return render(request, 'logistics/ficha_tecnica_form.html', {
        'form': form,
        'ficha': ficha,
        'titulo': f'Editar Ficha Técnica: {ficha.material.nombre}'
    })


# ============================================================
# CABECERA N:M — ÓRDENES DE DESPACHO
# ============================================================

def orden_despacho_list(request):
    # OPTIMIZACIÓN ORM: select_related para FK directas y prefetch_related para detalles con sus materiales
    despachos = OrdenDespacho.objects.select_related(
        'sucursal_destino',
        'transportista'
    ).prefetch_related(
        'detalles__material'
    ).all()
    return render(request, 'logistics/orden_despacho_list.html', {'despachos': despachos})


def orden_despacho_detail(request, pk):
    despacho = get_object_or_404(
        OrdenDespacho.objects.select_related('sucursal_destino', 'transportista').prefetch_related('detalles__material'),
        pk=pk
    )
    return render(request, 'logistics/orden_despacho_detail.html', {'despacho': despacho})


def orden_despacho_create(request):
    if request.method == 'POST':
        form = OrdenDespachoForm(request.POST)
        if form.is_valid():
            despacho = form.save()
            messages.success(request, f'Orden de despacho {despacho.codigo} creada. Ahora puede agregar materiales.')
            return redirect('logistics:orden_despacho_detail', pk=despacho.pk)
    else:
        form = OrdenDespachoForm()
    return render(request, 'logistics/orden_despacho_form.html', {
        'form': form,
        'titulo': 'Nueva Orden de Despacho Logístico'
    })


# Lab 7 - Parte 2 (Criterios 1 y 2): Crear despacho y descontar inventario en una transacción
def despacho_transaccional_view(request):
    form = RegistroDespachoForm(request.POST if request.method == 'POST' else None)
    # Lab 7 - Parte 2 (Criterio 7): Limitar el selector transaccional a materiales con stock positivo
    form.fields['material'].queryset = Material.objects.con_stock()

    if request.method == 'POST':
        if form.is_valid():
            datos = form.cleaned_data
            cantidad = datos['cantidad']

            try:
                # Lab 7 - Parte 2 (Criterios 1 y 2): Abrir atomicidad y bloquear la fila del material
                with transaction.atomic():
                    material = Material.objects.select_for_update().get(
                        pk=datos['material'].pk,
                    )
                    if material.stock < cantidad:
                        raise ValueError("Stock insuficiente")

                    # Lab 7 - Parte 2 (Criterios 1 y 2): Descontar stock con expresión F de forma atómica
                    stock_actualizado = Material.objects.filter(
                        pk=material.pk,
                        stock__gte=cantidad,
                    ).update(stock=F('stock') - cantidad)
                    if not stock_actualizado:
                        raise ValueError("Stock insuficiente")

                    # Lab 7 - Parte 2 (Criterios 1 y 2): Crear cabecera y detalle histórico del despacho
                    codigo = f"DSP-{uuid.uuid4().hex[:8].upper()}"
                    while OrdenDespacho.objects.filter(codigo=codigo).exists():
                        codigo = f"DSP-{uuid.uuid4().hex[:8].upper()}"

                    despacho = OrdenDespacho.objects.create(
                        codigo=codigo,
                        sucursal_destino=datos['sucursal'],
                        transportista=datos['transportista'],
                        estado='En Tránsito',
                        observaciones=datos['observaciones'],
                    )
                    DetalleDespacho.objects.create(
                        despacho=despacho,
                        material=material,
                        cantidad_despachada=cantidad,
                        costo_unitario_historico=material.precio_unitario,
                    )

                    # Lab 7 - Parte 2 (Criterios 1 y 2): Forzar fallo después de las escrituras para comprobar rollback
                    if datos['simular_error']:
                        raise Exception("Error forzado para comprobación de Rollback")
            except Exception as e:
                messages.error(request, str(e))
            else:
                messages.success(request, f"Despacho {despacho.codigo} creado correctamente.")
                return redirect('logistics:orden_despacho_list')
    # Lab 7 - Parte 2 (Criterios 1 y 2): Consultar órdenes recientes para comprobar el resultado
    despachos_recientes = OrdenDespacho.objects.select_related(
        'sucursal_destino', 'transportista'
    ).order_by('-fecha_emision')[:5]
    return render(request, 'logistics/despacho_form.html', {
        'form': form,
        'titulo': 'Registrar Despacho Transaccional',
        'despachos_recientes': despachos_recientes,
    })


def orden_despacho_update(request, pk):
    despacho = get_object_or_404(OrdenDespacho, pk=pk)
    if request.method == 'POST':
        form = OrdenDespachoForm(request.POST, instance=despacho)
        if form.is_valid():
            form.save()
            messages.success(request, f'Orden de despacho {despacho.codigo} actualizada.')
            return redirect('logistics:orden_despacho_detail', pk=despacho.pk)
    else:
        form = OrdenDespachoForm(instance=despacho)
    return render(request, 'logistics/orden_despacho_form.html', {
        'form': form,
        'titulo': f'Editar Orden de Despacho: {despacho.codigo}'
    })


def orden_despacho_delete(request, pk):
    despacho = get_object_or_404(OrdenDespacho, pk=pk)
    if request.method == 'POST':
        codigo = despacho.codigo
        despacho.delete()
        messages.warning(request, f'La orden de despacho {codigo} fue eliminada.')
        return redirect('logistics:orden_despacho_list')
    return render(request, 'logistics/orden_despacho_confirm_delete.html', {'objeto': despacho})


# ============================================================
# CRUD COMPLETO DEL MODELO INTERMEDIO: DETALLE DESPACHO (CRITERIO 9)
# ============================================================

def detalle_despacho_list(request):
    # READ: Consulta optimizada de todos los envíos intermedios
    detalles = DetalleDespacho.objects.select_related(
        'despacho',
        'despacho__sucursal_destino',
        'material'
    ).all()
    return render(request, 'logistics/detalle_despacho_list.html', {'detalles': detalles})


def detalle_despacho_create(request, despacho_id=None):
    # CREATE: Registro del modelo intermedio con sus atributos propios
    initial_data = {}
    despacho_obj = None
    if despacho_id:
        despacho_obj = get_object_or_404(OrdenDespacho, pk=despacho_id)
        initial_data['despacho'] = despacho_obj

    if request.method == 'POST':
        form = DetalleDespachoForm(request.POST)
        if form.is_valid():
            detalle = form.save()
            messages.success(
                request,
                f'Material "{detalle.material.nombre}" añadido al despacho {detalle.despacho.codigo}.'
            )
            return redirect('logistics:orden_despacho_detail', pk=detalle.despacho.pk)
    else:
        form = DetalleDespachoForm(initial=initial_data)

    return render(request, 'logistics/detalle_despacho_form.html', {
        'form': form,
        'despacho_obj': despacho_obj,
        'titulo': f'Añadir Material a Despacho' if not despacho_obj else f'Añadir Material a {despacho_obj.codigo}'
    })


def detalle_despacho_update(request, pk):
    # UPDATE: Modificación de atributos propios (cantidad, costo histórico, lote, observaciones)
    detalle = get_object_or_404(
        DetalleDespacho.objects.select_related('despacho', 'material'),
        pk=pk
    )
    if request.method == 'POST':
        form = DetalleDespachoForm(request.POST, instance=detalle)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Detalle de despacho ({detalle.material.nombre}) actualizado correctamente.'
            )
            return redirect('logistics:orden_despacho_detail', pk=detalle.despacho.pk)
    else:
        form = DetalleDespachoForm(instance=detalle)

    return render(request, 'logistics/detalle_despacho_form.html', {
        'form': form,
        'detalle': detalle,
        'titulo': f'Editar Item: {detalle.material.nombre} en {detalle.despacho.codigo}'
    })


def detalle_despacho_delete(request, pk):
    # DELETE: Eliminación segura del registro intermedio con confirmación
    detalle = get_object_or_404(
        DetalleDespacho.objects.select_related('despacho', 'material'),
        pk=pk
    )
    despacho_pk = detalle.despacho.pk
    if request.method == 'POST':
        material_nombre = detalle.material.nombre
        detalle.delete()
        messages.warning(
            request,
            f'Se retiró el material "{material_nombre}" de la orden de despacho.'
        )
        return redirect('logistics:orden_despacho_detail', pk=despacho_pk)
    return render(request, 'logistics/detalle_despacho_confirm_delete.html', {
        'objeto': detalle,
        'despacho_pk': despacho_pk
    })


# ============================================================
# CRUD: CATEGORÍAS (LADO 1 DE 1:N) Y PROVEEDORES
# ============================================================

def categoria_list(request):
    categorias = CategoriaInsumo.objects.prefetch_related('materiales').all()
    return render(request, 'logistics/categoria_list.html', {'categorias': categorias})


def categoria_create(request):
    if request.method == 'POST':
        form = CategoriaInsumoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría creada con éxito.")
            return redirect('logistics:categoria_list')
    else:
        form = CategoriaInsumoForm()
    return render(request, 'logistics/categoria_form.html', {'form': form, 'titulo': 'Nueva Categoría de Insumo'})


def categoria_delete(request, pk):
    categoria = get_object_or_404(CategoriaInsumo, pk=pk)
    if request.method == 'POST':
        try:
            categoria.delete()
            messages.warning(request, f'La categoría "{categoria.nombre}" fue eliminada.')
            return redirect('logistics:categoria_list')
        except ProtectedError:
            # Demostración del comportamiento de on_delete=models.PROTECT (Criterio 2)
            messages.error(
                request,
                f'Acción bloqueada: No se puede eliminar la categoría "{categoria.nombre}" '
                f'porque contiene insumos protegidos en inventario. Reasigne o elimine primero los materiales.'
            )
            return redirect('logistics:categoria_list')
    return render(request, 'logistics/categoria_confirm_delete.html', {'objeto': categoria})


def proveedor_list(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'logistics/proveedor_list.html', {'proveedores': proveedores})


def proveedor_create(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Proveedor registrado exitosamente.")
            return redirect('logistics:proveedor_list')
    else:
        form = ProveedorForm()
    return render(request, 'logistics/proveedor_form.html', {'form': form, 'titulo': 'Registrar Proveedor'})

