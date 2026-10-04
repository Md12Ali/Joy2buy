"""Form helpers shared by every app."""
from django import forms


class BootstrapFormMixin:
    """Add the matching Bootstrap 5 CSS class to every form widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css_class = "form-select"
            else:
                css_class = "form-control"
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css_class}".strip()


def tidy_text(value):
    """Collapse runs of whitespace and trim the ends of a text value."""
    return " ".join((value or "").split())
