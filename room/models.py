from django.db import models
from user.models import User


# Create your models here.
class Room(models.Model):
    name = models.CharField(max_length=127, unique=True)
    members = models.ManyToManyField(User, related_name="rooms")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Message(models.Model):
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')

    def __str__(self):
        return f'{self.author.username} - {self.room.name} - {self.content if len(self.content) < 25 else self.content[:25] + "..."}'


class UserStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=127,
        unique=False,
        choices=[
            ('owner', 'Propriétaire'),
            ('administrator', 'Administrateur'),
            ('user', 'Utilisateur'),
            ('muted', 'Muet'),
            ('banned', 'Banni')
        ],
        default='user'
    )

    class Meta:
        unique_together = ('user', 'room', 'status')

    def __str__(self):
        return f'{self.user.username} - {self.room.name} - {self.status}'


class Invitation(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    status = models.CharField(
        max_length=127,
        choices=[
            ('pending', 'En attente'),
            ('accepted', 'Acceptée'),
            ('declined', 'Refusée')
        ],
        default='pending'
    )

    class Meta:
        unique_together = ('room', 'sender', 'receiver')

    def __str__(self):
        return f'Invitation from {self.sender} to {self.receiver} for {self.room}'
