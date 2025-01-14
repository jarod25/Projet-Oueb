from django.db import models

# Create your models here.
class User(models.Model):
    mail = models.EmailField(unique=True)
    username = models.CharField(max_length=127, unique=True)
    password = models.CharField(max_length=127)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    def lower(self):
        return self.username.lower()