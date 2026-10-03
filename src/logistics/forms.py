from django import forms
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


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['ruc', 'razon_social', 'telefono', 'correo']
        widgets = {
            'ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 20123456789'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Textiles del Sur S.A.C.'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 987654321'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contacto@textiles.com'}),
        }

    def clean_ruc(self):
        ruc = self.cleaned_data.get('ruc')
        if ruc:
            ruc = ruc.strip()
            if not ruc.isdigit():
                raise forms.ValidationError("El RUC debe contener únicamente dígitos numéricos.")
            if len(ruc) != 11:
                raise forms.ValidationError("El RUC debe contener exactamente 11 dígitos numéricos.")
        return ruc


class SucursalForm(forms.ModelForm):
    class Meta:
        model = Sucursal
        fields = ['nombre', 'direccion', 'ciudad', 'capacidad_almacen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Almacén Central Lima'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Av. Argentina 1234'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Lima'}),
            'capacidad_almacen': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class TransportistaForm(forms.ModelForm):
    class Meta:
        model = Transportista
        fields = ['empresa', 'placa', 'tipo_vehiculo', 'activo']
        widgets = {
            'empresa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Express Cargo SAC'}),
            'placa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. ABC-123'}),
            'tipo_vehiculo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Camión 5TN'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_placa(self):
        placa = self.cleaned_data.get('placa')
        if placa:
            return placa.strip().upper()
        return placa


class CategoriaInsumoForm(forms.ModelForm):
    class Meta:
        model = CategoriaInsumo
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Telas e Hilados'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción técnica...'}),
        }


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['categoria', 'nombre', 'unidad_medida', 'precio_unitario', 'stock']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Tela Algodón Pima 50/1'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Metros / Conos / Rollos'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def clean_precio_unitario(self):
        precio = self.cleaned_data.get('precio_unitario')
        if precio is not None and precio <= 0:
            raise forms.ValidationError("El precio unitario debe ser mayor a cero.")
        return precio


# ============================================================
# FORMULARIOS PARA RELACIONES AVANZADAS (PARTE 2)
# ============================================================

class FichaTecnicaMaterialForm(forms.ModelForm):
    class Meta:
        model = FichaTecnicaMaterial
        fields = [
            'material',
            'composicion',
            'densidad_gramaje',
            'tolerancia_encogimiento',
            'temperatura_lavado',
            'cuidados_adicionales'
        ]
        widgets = {
            'material': forms.Select(attrs={'class': 'form-select'}),
            'composicion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 100% Algodón Pima'}),
            'densidad_gramaje': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 240 gr/m²'}),
            'tolerancia_encogimiento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. +/- 2.5%'}),
            'temperatura_lavado': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Lavar en agua fría (30°C)'}),
            'cuidados_adicionales': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Recomendaciones textiles...'}),
        }


class OrdenDespachoForm(forms.ModelForm):
    class Meta:
        model = OrdenDespacho
        fields = ['codigo', 'sucursal_destino', 'transportista', 'estado', 'observaciones']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. DSP-2026-001'}),
            'sucursal_destino': forms.Select(attrs={'class': 'form-select'}),
            'transportista': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notas de envío...'}),
        }

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            return codigo.strip().upper()
        return codigo


class DetalleDespachoForm(forms.ModelForm):
    class Meta:
        model = DetalleDespacho
        fields = [
            'despacho',
            'material',
            'cantidad_despachada',
            'costo_unitario_historico',
            'lote_produccion',
            'observaciones'
        ]
        widgets = {
            'despacho': forms.Select(attrs={'class': 'form-select'}),
            'material': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_despachada': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'costo_unitario_historico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'lote_produccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. LOTE-2026-TX01'}),
            'observaciones': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Observaciones de entrega...'}),
        }

    def clean_cantidad_despachada(self):
        cantidad = self.cleaned_data.get('cantidad_despachada')
        if cantidad is not None and cantidad <= 0:
            raise forms.ValidationError("La cantidad despachada debe ser un número entero mayor a cero.")
        return cantidad

    def clean_costo_unitario_historico(self):
        costo = self.cleaned_data.get('costo_unitario_historico')
        if costo is not None and costo <= 0:
            raise forms.ValidationError("El costo unitario histórico debe ser mayor a cero.")
        return costo

    def clean_lote_produccion(self):
        lote = self.cleaned_data.get('lote_produccion')
        if lote:
            return lote.strip().upper()
        return lote


# Lab 7 - Parte 2 (Criterios 1 y 2): Formulario para registrar despachos transaccionales
class RegistroDespachoForm(forms.Form):
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.all(),
        required=True,
        label="Sucursal de destino",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    transportista = forms.ModelChoiceField(
        queryset=Transportista.objects.filter(activo=True),
        required=False,
        label="Transportista",
        empty_label="Sin asignar",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    material = forms.ModelChoiceField(
        queryset=Material.objects.all(),
        required=True,
        label="Material",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    cantidad = forms.IntegerField(
        min_value=1,
        required=True,
        label="Cantidad a despachar",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'step': 1}),
    )
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False,
        label="Observaciones",
    )
    simular_error = forms.BooleanField(
        required=False,
        label="Simular error para probar Rollback",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

