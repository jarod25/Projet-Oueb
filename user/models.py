from django.core.validators import EmailValidator, MinLengthValidator
from django.db import models


# Create your models here.
class User(models.Model):
    mail = models.EmailField(
        unique=True,
        validators=[EmailValidator()]
    )
    username = models.CharField(
        max_length=127,
        unique=True,
        validators=[MinLengthValidator(5)]
    )
    password = models.CharField(
        max_length=127,
        validators=[MinLengthValidator(8)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    def lower(self):
        return self.username.lower()
