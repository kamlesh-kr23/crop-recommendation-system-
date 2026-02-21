from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Prediction(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='predictions'
    )

    # Soil Nutrients
    N = models.FloatField(validators=[MinValueValidator(0)])
    P = models.FloatField(validators=[MinValueValidator(0)])
    K = models.FloatField(validators=[MinValueValidator(0)])

    # Weather Parameters
    temperature = models.FloatField()
    humidity = models.FloatField()
    ph = models.FloatField()
    rainfall = models.FloatField()

    # ML Output
    predicted_label = models.CharField(max_length=100)

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Prediction"
        verbose_name_plural = "Predictions"

    def __str__(self):
        return f"{self.user.username} -> {self.predicted_label}"
