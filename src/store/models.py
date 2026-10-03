from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

#Implementación de memoria
from django.db.models.signals import post_save
from django.dispatch import receiver


# ============================================================
# Funciones del Laboratorio de la Semana 2 (almacenamiento en
# memoria). Se conservan comentadas como evidencia del código
# anterior; ya no se usan porque la persistencia ahora se
# maneja mediante el Model Prenda y Django ORM (Semana 3).
# ============================================================

# PRENDAS = [
#     {
#         'id': 1,
#         'nombre': 'Polo Oversize Rebel Classic',
#         'marca': 'Rebel',
#         'categoria': 'Polos',
#         'tipo': 'Unisex',
#         'talla': 'L',
#         'precio': 89.90,
#         'stock': 20,
#         'disponible': True,
#         'descripcion': 'Polo oversize de algodón peruano 100%, corte streetwear con logo bordado en el pecho.',
#     },
#     {
#         'id': 2,
#         'nombre': 'Hoodie Doggis Street Corp',
#         'marca': 'Doggis Clothing',
#         'categoria': 'Casacas y Poleras',
#         'tipo': 'Hombre',
#         'talla': 'M',
#         'precio': 159.90,
#         'stock': 8,
#         'disponible': True,
#         'descripcion': 'Buzo con capucha en French Terry, print frontal serigrafiado y bolsillo canguro.',
#     },
#     {
#         'id': 3,
#         'nombre': 'Jean Baggy Rasec Wide Leg',
#         'marca': 'Rasec',
#         'categoria': 'Jeans',
#         'tipo': 'Unisex',
#         'talla': '32',
#         'precio': 179.00,
#         'stock': 0,
#         'disponible': True,
#         'descripcion': 'Jean de corte ancho (baggy) en denim rígido, tiro medio, silueta skater.',
#     },
#     {
#         'id': 4,
#         'nombre': 'Casaca Selva Alegre Windbreaker',
#         'marca': 'Selva Alegre',
#         'categoria': 'Casacas y Poleras',
#         'tipo': 'Unisex',
#         'talla': 'XL',
#         'precio': 219.90,
#         'stock': 5,
#         'disponible': True,
#         'descripcion': 'Rompevientos ligero con capucha, inspirado en la identidad amazónica de la marca.',
#     },
#     {
#         'id': 5,
#         'nombre': 'Polera Cosa Nostra Crewneck',
#         'marca': 'Cosa Nostra',
#         'categoria': 'Casacas y Poleras',
#         'tipo': 'Hombre',
#         'talla': 'M',
#         'precio': 139.90,
#         'stock': 12,
#         'disponible': True,
#         'descripcion': 'Crewneck en fleece pesado con bordado del logo característico en la manga.',
#     },
#     {
#         'id': 6,
#         'nombre': 'Polo Box Fit Mugre Basics',
#         'marca': 'Mugre',
#         'categoria': 'Polos',
#         'tipo': 'Unisex',
#         'talla': 'S',
#         'precio': 69.90,
#         'stock': 15,
#         'disponible': True,
#         'descripcion': 'Polo de corte cuadrado (box fit) en algodón peinado 24/1, tela pesada.',
#     },
#     {
#         'id': 7,
#         'nombre': 'Short Cargo Rebel Utility',
#         'marca': 'Rebel',
#         'categoria': 'Ropa Deportiva',
#         'tipo': 'Hombre',
#         'talla': '30',
#         'precio': 109.90,
#         'stock': 3,
#         'disponible': True,
#         'descripcion': 'Short cargo con bolsillos laterales tipo cartuchera y cordón ajustable.',
#     },
#     {
#         'id': 8,
#         'nombre': 'Vestido Oversized Tee Dress Rasec',
#         'marca': 'Rasec',
#         'categoria': 'Vestidos',
#         'tipo': 'Mujer',
#         'talla': 'Única',
#         'precio': 99.90,
#         'stock': 7,
#         'disponible': True,
#         'descripcion': 'Vestido tipo camiseta extralarga, silueta oversize, ideal para looks casuales.',
#     },
#     {
#         'id': 9,
#         'nombre': 'Casaca Denim Doggis Vintage Wash',
#         'marca': 'Doggis Clothing',
#         'categoria': 'Casacas y Poleras',
#         'tipo': 'Unisex',
#         'talla': 'L',
#         'precio': 189.90,
#         'stock': 4,
#         'disponible': False,
#         'descripcion': 'Casaca de mezclilla con lavado vintage y parche bordado en la espalda.',
#     },
#     {
#         'id': 10,
#         'nombre': 'Polo Niños Selva Alegre Mini',
#         'marca': 'Selva Alegre',
#         'categoria': 'Polos',
#         'tipo': 'Niños',
#         'talla': '8-10',
#         'precio': 59.90,
#         'stock': 10,
#         'disponible': True,
#         'descripcion': 'Versión infantil del polo insignia de la marca, algodón suave hipoalergénico.',
#     },
# ]
#
# def obtener_prendas():
#     return PRENDAS
#
# def obtener_prenda_por_id(prenda_id):
#     return next((p for p in PRENDAS if p['id'] == prenda_id), None)
#
# def agregar_prenda(nueva_prenda):
#     nueva_prenda['id'] = max((p['id'] for p in PRENDAS), default=0) + 1
#     PRENDAS.append(nueva_prenda)
#     return nueva_prenda


TIPOS_CHOICES = [
    ('Hombre', 'Moda Hombre'),
    ('Mujer', 'Moda Mujer'),
    ('Niños', 'Moda Infantil / Niños'),
    ('Unisex', 'Línea Unisex'),
]

CATEGORIAS_CHOICES = [
    ('Polos', 'Polos y Camisas'),
    ('Jeans', 'Pantalones y Jeans'),
    ('Casacas y Poleras', 'Casacas y Poleras'),
    ('Vestidos', 'Vestidos y Faldas'),
    ('Ropa Deportiva', 'Ropa Deportiva'),
    ('Calzado', 'Calzado'),
]

TALLAS_CHOICES = [
    ('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'),
    ('28', '28'), ('30', '30'), ('32', '32'), ('34', '34'),
    ('4-6', '4-6 años'), ('8-10', '8-10 años'), ('12-14', '12-14 años'),
    ('Única', 'Talla Única'),
]


# Lab 7 - Ejercicio 7: QuerySet encadenable para filtrar prendas activas y disponibles
class PrendaQuerySet(models.QuerySet):
    # Lab 7 - Ejercicio 7: Filtro reutilizable de prendas activas
    def activas(self):
        return self.filter(activo=True)

    # Lab 7 - Ejercicio 7: Filtro encadenable de prendas disponibles con stock
    def disponibles(self):
        return self.filter(disponible=True, stock__gt=0)


class Prenda(models.Model):
    # Lab 7 - Ejercicio 7: QuerySet personalizado asignado como manager
    objects = PrendaQuerySet.as_manager()

    nombre = models.CharField(max_length=120)
    marca = models.CharField(max_length=80)
    tipo = models.CharField(max_length=20, choices=TIPOS_CHOICES)
    categoria = models.CharField(max_length=40, choices=CATEGORIAS_CHOICES)
    talla = models.CharField(max_length=10, choices=TALLAS_CHOICES)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    disponible = models.BooleanField(default=True)
    activo = models.BooleanField(default=True, help_text="Indica si el registro está activo en el sistema o archivado")
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class DetallePrenda(models.Model):
    prenda = models.OneToOneField(
        Prenda,
        on_delete=models.CASCADE,
        related_name='detalle',
        verbose_name="Prenda"
    )
    composicion = models.CharField(
        max_length=200,
        verbose_name="Composición Textil",
        help_text="Ej: 100% Algodón Peinado 24/1"
    )
    cuidados = models.TextField(
        verbose_name="Instrucciones de Cuidado",
        help_text="Ej: Lavar con agua fría, secar a la sombra, no usar lejía"
    )
    pais_origen = models.CharField(
        max_length=60,
        default="Perú",
        verbose_name="País de Origen"
    )
    guia_medidas = models.TextField(
        blank=True,
        verbose_name="Guía de Medidas / Dimensiones",
        help_text="Ej: Pecho: 56cm | Largo: 74cm | Manga: 22cm"
    )

    class Meta:
        verbose_name = "Detalle de Prenda"
        verbose_name_plural = "Detalles de Prendas"

    def __str__(self):
        return f"Detalle de {self.prenda.nombre}"


class ResenaPrenda(models.Model):
    prenda = models.ForeignKey(
        Prenda,
        on_delete=models.CASCADE,
        related_name='resenas',
        verbose_name="Prenda calificada"
    )
    cliente_nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del Cliente"
    )
    calificacion = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Calificación (Estrellas)",
        help_text="Puntuación del 1 al 5"
    )
    comentario = models.TextField(
        verbose_name="Comentario u Opinión"
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de publicación"
    )

    class Meta:
        verbose_name = "Reseña de Prenda"
        verbose_name_plural = "Reseñas de Prendas"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.cliente_nombre} - {self.prenda.nombre} ({self.calificacion}★)"


ESTADO_PEDIDO_CHOICES = [
    ('Pendiente', 'Pendiente de Pago'),
    ('Pagado', 'Pagado / En Preparación'),
    ('Enviado', 'Enviado en Reparto'),
    ('Entregado', 'Entregado al Cliente'),
    ('Cancelado', 'Cancelado'),
]


class Pedido(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código de Pedido")
    cliente_nombre = models.CharField(max_length=100, verbose_name="Nombre del Cliente")
    cliente_email = models.EmailField(verbose_name="Correo Electrónico")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    estado = models.CharField(max_length=20, choices=ESTADO_PEDIDO_CHOICES, default='Pendiente', verbose_name="Estado")
    prendas = models.ManyToManyField(
        Prenda,
        through='DetallePedido',
        related_name='pedidos',
        verbose_name="Prendas Incluidas"
    )

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Pedido {self.codigo} - {self.cliente_nombre} ({self.estado})"

    def total(self):
        return sum(d.subtotal() for d in self.detalles.all())


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Pedido"
    )
    prenda = models.ForeignKey(
        Prenda,
        on_delete=models.CASCADE,
        related_name='detalles_pedido',
        verbose_name="Prenda"
    )
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Precio Unitario (S/)")
    fecha_agregado = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Agregado")

    class Meta:
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedidos"
        unique_together = ('pedido', 'prenda')

    def __str__(self):
        return f"{self.cantidad}x {self.prenda.nombre} en {self.pedido.codigo}"

    def subtotal(self):
        return self.cantidad * self.precio_unitario


# Crea automaticamente la ficha tecnica 1:1 al registrar una prenda.
# Debe estar fuera de las clases para registrarse a nivel de modulo.
@receiver(post_save, sender=Prenda)
def crear_o_actualizar_detalle_prenda(sender, instance, created, **kwargs):
    """
    Cada vez que se crea una nueva Prenda, se genera automáticamente
    su registro complementario 1:1 en DetallePrenda con valores acordes
    a su categoría.
    """
    if getattr(instance, '_from_admin', False) or DetallePrenda.objects.filter(prenda=instance).exists():
        return
    if created:

        especificaciones = {
            'Polos': {
                'composicion': '100% Algodón Peinado 24/1',
                'cuidados': 'Lavar con agua fría, secar a la sombra, planchar a temperatura media',
            },
            'Casacas y Poleras': {
                'composicion': 'Algodón French Terry con poliéster (Fleece pesado)',
                'cuidados': 'Lavar al revés con agua fría, no usar lejía',
            },
            'Jeans': {
                'composicion': '100% Denim rígido 13 oz',
                'cuidados': 'Lavar por separado en agua fría, secar tendido',
            },
            'Ropa Deportiva': {
                'composicion': 'Drill Stretch / Poliéster técnico',
                'cuidados': 'Lavado suave, secado rápido, no planchar estampados',
            },
            'Vestidos': {
                'composicion': '100% Algodón Jersey suave',
                'cuidados': 'Lavar en ciclo delicado, no estrujar',
            },
        }

        config = especificaciones.get(instance.categoria, {
            'composicion': 'Algodón nacional seleccionado',
            'cuidados': 'Lavar con agua fría y colores similares',
        })

        DetallePrenda.objects.create(
            prenda=instance,
            composicion=config['composicion'],
            cuidados=config['cuidados'],
            pais_origen='Perú',
            guia_medidas=f'Talla estándar {instance.talla}'
        )