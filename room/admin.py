from django.contrib import admin
from .models import Room, Status, Message, UserStatus

# Register your models here.
admin.site.register(Room)
admin.site.register(Status)
admin.site.register(Message)
admin.site.register(UserStatus)