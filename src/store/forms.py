from django import forms

TIPOS_CHOICES = [
    ('', '-- Seleccione Público / Tipo --'),
    ('Hombre', 'Moda Hombre'),
    ('Mujer', 'Moda Mujer'),
    ('Niños', 'Moda Infantil / Niños'),
    ('Unisex', 'Línea Unisex'),
]

CATEGORIAS_CHOICES = [
    ('', '-- Seleccione Categoría --'),
    ('Polos', 'Polos y Camisas'),
    ('Jeans', 'Pantalones y Jeans'),
    ('Casacas y Poleras', 'Casacas y Poleras'),
    ('Vestidos', 'Vestidos y Faldas'),
    ('Ropa Deportiva', 'Ropa Deportiva'),
    ('Calzado', 'Calzado'),
]

TALLAS_CHOICES = [
    ('', '-- Seleccione Talla --'),
    ('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'),
    ('28', '28'), ('30', '30'), ('32', '32'), ('34', '34'),
    ('4-6', '4-6 años'), ('8-10', '8-10 años'), ('12-14', '12-14 años'),
    ('Única', 'Talla Única'),
]


class PrendaForm(forms.Form):
    nombre = forms.CharField(
        max_length=120,
        required=True,
        label="Nombre del Producto",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Polo Oversize Rebel Classic'})
    )
    marca = forms.CharField(
        max_length=80,
        required=True,
        label="Marca / Fabricante",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Rebel'})
    )
    tipo = forms.ChoiceField(
        choices=TIPOS_CHOICES,
        required=True,
        label="Público / Tipo",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    categoria = forms.ChoiceField(
        choices=CATEGORIAS_CHOICES,
        required=True,
        label="Categoría",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    talla = forms.ChoiceField(
        choices=TALLAS_CHOICES,
        required=True,
        label="Talla",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    precio = forms.DecimalField(
        required=True,
        min_value=0,
        label="Precio (S/)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.10'})
    )
    stock = forms.IntegerField(
        required=True,
        min_value=0,
        label="Stock",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    disponible = forms.BooleanField(
        required=False,
        initial=True,
        label="Disponible para venta"
    )
    activo = forms.BooleanField(
        required=False,
        initial=True,
        label="Activo en el catálogo (Habilitado)"
    )
    descripcion = forms.CharField(
        required=False,
        label="Descripción",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


ESTRELLAS_CHOICES = [
    (5, '★★★★★ (5 estrellas - Excelente)'),
    (4, '★★★★☆ (4 estrellas - Muy Bueno)'),
    (3, '★★★☆☆ (3 estrellas - Bueno)'),
    (2, '★★☆☆☆ (2 estrellas - Regular)'),
    (1, '★☆☆☆☆ (1 estrella - Malo)'),
]


class ResenaPrendaForm(forms.Form):
    cliente_nombre = forms.CharField(
        max_length=100,
        required=True,
        label="Tu Nombre",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Carlos Mendoza'})
    )
    calificacion = forms.ChoiceField(
        choices=ESTRELLAS_CHOICES,
        required=True,
        label="Calificación",
        initial=5,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    comentario = forms.CharField(
        required=True,
        label="Tu Opinión sobre la Prenda",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Cuéntanos qué tal te pareció la tela, corte o talla...'})
    )
