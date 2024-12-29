from django.contrib import admin
from .models import Room, Status, Message, UserStatus, Invitation

# Register your models here.
admin.site.register(Room)
admin.site.register(Status)
admin.site.register(Message)
admin.site.register(UserStatus)
admin.site.register(Invitation)