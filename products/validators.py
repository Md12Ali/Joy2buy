"""Reusable field validators."""
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_image_size(image):
    """Reject uploads larger than ``settings.MAX_IMAGE_UPLOAD_BYTES``."""
    limit = settings.MAX_IMAGE_UPLOAD_BYTES
    size = getattr(image, "size", 0) or 0
    if size > limit:
        megabytes = limit / (1024 * 1024)
        raise ValidationError(
            f"Image files must be {megabytes:.0f} MB or smaller."
        )
