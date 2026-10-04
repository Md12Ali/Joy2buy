"""Forms for the catalogue: products, categories and reviews."""
from django import forms

from joy2buy.forms import BootstrapFormMixin, tidy_text

from .models import Category, Product, ProductReview


class CategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "image"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def clean_name(self):
        name = tidy_text(self.cleaned_data.get("name"))
        if len(name) < 2:
            raise forms.ValidationError(
                "Category names need at least 2 characters."
            )
        duplicate = Category.objects.filter(name__iexact=name)
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError(
                "A category with this name already exists."
            )
        return name


class ProductForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "category",
            "name",
            "description",
            "specifications",
            "price",
            "stock",
            "image",
            "status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "specifications": forms.Textarea(attrs={"rows": 5}),
            "price": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"min": "0", "step": "1"}),
        }

    def clean_name(self):
        name = tidy_text(self.cleaned_data.get("name"))
        if len(name) < 3:
            raise forms.ValidationError(
                "Product names need at least 3 characters."
            )
        return name

    def clean_description(self):
        description = (self.cleaned_data.get("description") or "").strip()
        if len(description) < 20:
            raise forms.ValidationError(
                "Please describe the product in at least 20 characters."
            )
        return description

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is None or price <= 0:
            raise forms.ValidationError("The price must be above zero.")
        return price


class ReviewForm(BootstrapFormMixin, forms.ModelForm):
    RATING_CHOICES = [
        ("", "Choose a rating"),
        (5, "5 - Excellent"),
        (4, "4 - Good"),
        (3, "3 - Average"),
        (2, "2 - Poor"),
        (1, "1 - Terrible"),
    ]

    rating = forms.TypedChoiceField(
        choices=RATING_CHOICES,
        coerce=int,
        label="Your rating",
        error_messages={"required": "Please choose a star rating."},
    )

    class Meta:
        model = ProductReview
        fields = ["rating", "text"]
        labels = {"text": "Your review"}
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 4,
                    "maxlength": 1000,
                    "placeholder": "What did you like or dislike?",
                }
            ),
        }

    def clean_text(self):
        text = (self.cleaned_data.get("text") or "").strip()
        if len(text) < 10:
            raise forms.ValidationError(
                "Please write at least 10 characters so your review is "
                "useful to other shoppers."
            )
        return text
