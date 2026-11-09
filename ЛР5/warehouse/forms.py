from django import forms

from .models import Movement


class MovementForm(forms.ModelForm):
    class Meta:
        model = Movement
        fields = ["movement_type", "product", "quantity", "device"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if quantity < 1:
            raise forms.ValidationError("Кількість має бути не менше 1.")
        return quantity

    def clean(self):
        data = super().clean()
        product, quantity = data.get("product"), data.get("quantity")
        if data.get("movement_type") == "out" and product and quantity and quantity > product.quantity:
            raise forms.ValidationError(f"На складі лише {product.quantity} шт. товару {product.sku}.")
        return data
