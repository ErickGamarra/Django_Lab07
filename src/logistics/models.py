from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# 1. ENTIDADES INDEPENDIENTES

class Proveedor(models.Model):
    ruc = models.CharField(max_length=11, unique=True, verbose_name="RUC")
    razon_social = models.CharField(max_length=120, verbose_name="Razón Social")
    telefono = models.CharField(max_length=15, verbose_name="Teléfono")
    correo = models.EmailField(verbose_name="Correo Electrónico")

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['razon_social']

    def __str__(self):
        return f"{self.razon_social} ({self.ruc})"


class Sucursal(models.Model):
    nombre = models.CharField(max_length=80, verbose_name="Nombre de Sede")
    direccion = models.CharField(max_length=150, verbose_name="Dirección")
    ciudad = models.CharField(max_length=50, verbose_name="Ciudad")
    capacidad_almacen = models.PositiveIntegerField(verbose_name="Capacidad de Almacén (unidades)")

    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.ciudad}"


class Transportista(models.Model):
    empresa = models.CharField(max_length=100, verbose_name="Empresa de Transporte")
    placa = models.CharField(max_length=10, unique=True, verbose_name="Número de Placa")
    tipo_vehiculo = models.CharField(max_length=30, verbose_name="Tipo de Vehículo")
    activo = models.BooleanField(default=True, verbose_name="Operativo / Activo")

    class Meta:
        verbose_name = "Transportista"
        verbose_name_plural = "Transportistas"
        ordering = ['empresa']

    def __str__(self):
        return f"{self.empresa} [{self.placa}]"


# 2. ENTIDADES RELACIONADAS (1:N)

class CategoriaInsumo(models.Model):
    nombre = models.CharField(max_length=60, unique=True, verbose_name="Nombre de Categoría")
    descripcion = models.TextField(blank=True, verbose_name="Descripción Técnica")

    class Meta:
        verbose_name = "Categoría de Insumo"
        verbose_name_plural = "Categorías de Insumos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


# Lab 7 - Parte 2 (Criterio 6): QuerySet personalizado para Material
class MaterialQuerySet(models.QuerySet):
    # Lab 7 - Parte 2 (Criterio 6): Filtrar materiales con stock positivo
    def con_stock(self):
        return self.filter(stock__gt=0)

    # Lab 7 - Parte 2 (Criterio 6): Filtrar materiales por debajo del umbral indicado
    def stock_bajo(self, umbral=100):
        return self.filter(stock__lte=umbral)


class Material(models.Model):
    # Lab 7 - Parte 2 (Criterio 6): Asignar el QuerySet personalizado como manager
    objects = MaterialQuerySet.as_manager()

    categoria = models.ForeignKey(
        CategoriaInsumo,
        on_delete=models.PROTECT,
        related_name='materiales',
        verbose_name="Categoría Asignada"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Insumo")
    unidad_medida = models.CharField(max_length=20, verbose_name="Unidad de Medida")
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Precio Unitario (S/)")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock en Almacén")

    class Meta:
        verbose_name = "Material / Insumo"
        verbose_name_plural = "Materiales / Insumos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.categoria.nombre})"


# ============================================================
# 3. RELACIÓN 1:1 — Ficha Técnica Textil (FichaTecnicaMaterial)
# ============================================================
class FichaTecnicaMaterial(models.Model):
    material = models.OneToOneField(
        Material,
        on_delete=models.CASCADE,
        related_name='ficha_tecnica',
        verbose_name="Material Textil"
    )
    composicion = models.CharField(
        max_length=150,
        default="100% Algodón Peruano",
        verbose_name="Composición Textil"
    )
    densidad_gramaje = models.CharField(
        max_length=60,
        default="220 gr/m²",
        verbose_name="Densidad / Gramaje"
    )
    tolerancia_encogimiento = models.CharField(
        max_length=40,
        default="+/- 3%",
        verbose_name="Tolerancia de Encogimiento"
    )
    temperatura_lavado = models.CharField(
        max_length=60,
        default="Máximo 30°C",
        verbose_name="Temperatura de Lavado"
    )
    cuidados_adicionales = models.TextField(
        blank=True,
        default="No usar lejía. Secar a la sombra en superficie plana.",
        verbose_name="Cuidados Adicionales"
    )
    fecha_emision_certificado = models.DateField(
        auto_now_add=True,
        verbose_name="Fecha de Emisión"
    )

    class Meta:
        verbose_name = "Ficha Técnica de Material"
        verbose_name_plural = "Fichas Técnicas de Materiales"

    def __str__(self):
        return f"Ficha Técnica: {self.material.nombre}"


# Señal: Creación automática de Ficha Técnica al crear un Material
@receiver(post_save, sender=Material)
def auto_crear_ficha_tecnica(sender, instance, created, **kwargs):
    if getattr(instance, '_from_admin', False) or FichaTecnicaMaterial.objects.filter(material=instance).exists():
        return
    if created:
        FichaTecnicaMaterial.objects.create(material=instance)



# ============================================================
# 4. RELACIÓN N:M CON MODELO INTERMEDIO (OrdenDespacho y DetalleDespacho)
# ============================================================
class OrdenDespacho(models.Model):
    ESTADOS_DESPACHO = [
        ('Borrador', 'Borrador'),
        ('En Tránsito', 'En Tránsito'),
        ('Entregado', 'Entregado'),
        ('Cancelado', 'Cancelado'),
    ]

    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Código de Despacho"
    )
    sucursal_destino = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='despachos',
        verbose_name="Sucursal de Destino"
    )
    transportista = models.ForeignKey(
        Transportista,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='despachos',
        verbose_name="Transportista Asignado"
    )
    fecha_emision = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Emisión"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_DESPACHO,
        default='Borrador',
        verbose_name="Estado de Despacho"
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones de Guía"
    )
    materiales = models.ManyToManyField(
        Material,
        through='DetalleDespacho',
        related_name='ordenes_despacho',
        verbose_name="Materiales Despachados"
    )

    class Meta:
        verbose_name = "Orden de Despacho"
        verbose_name_plural = "Órdenes de Despacho"
        ordering = ['-fecha_emision']

    def __str__(self):
        return f"{self.codigo} -> {self.sucursal_destino.nombre} ({self.estado})"

    @property
    def total_unidades(self):
        return sum(d.cantidad_despachada for d in self.detalles.all())

    @property
    def costo_total(self):
        return sum(d.subtotal for d in self.detalles.all())


class DetalleDespacho(models.Model):
    despacho = models.ForeignKey(
        OrdenDespacho,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Orden de Despacho"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='detalles_despacho',
        verbose_name="Material Textil"
    )
    # Atributos propios de la relación que no pertenecen a ninguna entidad por separado:
    cantidad_despachada = models.PositiveIntegerField(
        verbose_name="Cantidad Despachada"
    )
    costo_unitario_historico = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Costo Unitario Histórico (S/)"
    )
    lote_produccion = models.CharField(
        max_length=30,
        default="LOTE-001",
        verbose_name="Número de Lote"
    )
    observaciones = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Notas de Recepción"
    )

    class Meta:
        verbose_name = "Detalle de Despacho"
        verbose_name_plural = "Detalles de Despacho"
        unique_together = ('despacho', 'material')

    @property
    def subtotal(self):
        return self.cantidad_despachada * self.costo_unitario_historico

    def __str__(self):
        return f"{self.despacho.codigo} | {self.material.nombre} ({self.cantidad_despachada} {self.material.unidad_medida})"

