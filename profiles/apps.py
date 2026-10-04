from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "profiles"

    def ready(self):
        # Connect the handler that gives every new user a profile.
        from . import signals  # noqa: F401
