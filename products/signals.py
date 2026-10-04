"""Keep ``Product.rating`` in step with its reviews."""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Product, ProductReview


@receiver(post_save, sender=ProductReview)
@receiver(post_delete, sender=ProductReview)
def refresh_product_rating(sender, instance, **kwargs):
    """Recalculate the average whenever a review is saved or removed."""
    product = Product.objects.filter(pk=instance.product_id).first()
    if product is not None:
        product.update_rating()
