from django.db import models

# Create your models here.
class Room(models.Model):
    name = models.CharField(max_length=127, unique=True)
    members = models.ManyToManyField('user.User', related_name="rooms")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Status(models.Model):
    label = models.CharField(
        max_length=127,
        unique=True,
        choices=[
            ('owner', 'Propriétaire'),
            ('administrator', 'Administrateur'),
            ('user', 'Utilisateur'),
            ('muted', 'Muet'),
            ('banned', 'Banni')
        ],
        default='user'
    )

    def __str__(self):
        return self.label

class Message(models.Model):
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='messages')

    def __str__(self):
        return f'{self.author.username} - {self.room.name} - {self.content if len(self.content) < 25 else self.content[:25] + "..."}'

class UserStatus(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('user', 'room')

    def __str__(self):
        return f'{self.user.username} - {self.room.name} - {self.status.label}'

class Invitation(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    sender = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='sent_invitations')
    receiver = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='received_invitations')
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