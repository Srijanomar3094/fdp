from django.db import models


class DeletedManager(models.Manager):
    """Default manager that excludes soft-deleted records (status=False)."""

    def get_queryset(self):
        return super().get_queryset().filter(status=True)


class BaseModel(models.Model):
    """
    Abstract base model providing soft delete, created/updated timestamps.

    status=True  → active record
    status=False → soft-deleted record (excluded from default queryset)

    Usage:
        MyModel.objects.all()          # active only (via DeletedManager)
        MyModel.all_objects.all()      # all records including deleted
        instance.soft_delete()         # mark as deleted without DB removal
    """
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DeletedManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.status = False
        self.save(update_fields=['status', 'updated_at'])
