from user.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from .models import Room, Invitation, UserStatus, Message
from user import login_required


@login_required
def room_list_view(request):
    user_id = request.session.get('user_id')
    user = User.objects.get(id=user_id)
    
    # Filtrer les salons où l'utilisateur est membre
    user_rooms = Room.objects.filter(members=user)
    
    return render(request, "room_list.html", {"rooms": user_rooms})


@login_required
def create_room_view(request):
    if request.method == "POST":
        # Récupérer le nom du salon à partir du formulaire
        room_name = request.POST.get("name")
        user_id = request.session.get('user_id')
        user = User.objects.get(id=user_id)
        # Vérifier si un salon avec le même nom existe déjà
        if Room.objects.filter(name=room_name).exists():
            return render(request, "create_room.html", {
                "error": "Un salon avec ce nom existe déjà."
            })

        # Créer le salon
        room = Room.objects.create(name=room_name)

        # Ajouter l'utilisateur comme membre du salon
        room.members.add(user)

        # Définir l'utilisateur comme propriétaire (owner) avec le modèle UserStatus
        UserStatus.objects.create(user=user, room=room, status="owner")

        # Rediriger vers la liste des salons après création
        return redirect("room_list")

    # Afficher la page de création de salon pour les requêtes GET
    return render(request, "create_room.html")

@login_required
def delete_room_view(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    room.delete()
    return redirect("room_list")

@login_required
def room_detail_view(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    messages = room.messages.order_by('sent_at', 'id')
    rooms = Room.objects.all()  # Liste des salons
    return render(request, "room_details.html", {
        "room": room,
        "messages": messages,
        "rooms": rooms
    })


@require_POST
@login_required
def send_message_view(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    user = User.objects.get(id=request.session.get('user_id'))
    content_message = request.POST.get("content")

    if content_message:
        Message.objects.create(content=content_message, room=room, author=user)

    # Redirige vers la même page pour éviter tout problème de double affichage
    return redirect("room_detail", room_id=room.id)

def search_users(request, room_id):
    user = User.objects.get(id=request.session.get('user_id'))
    query = request.GET.get("q")
    users = User.objects.exclude(id=user.id).filter(username__icontains=query)
    results = [user.username for user in users]
    return JsonResponse(results, safe=False)


@login_required
def invite_user_view(request, room_id):
    user = User.objects.get(id=request.session.get('user_id'))
    room = get_object_or_404(Room, id=room_id)

    if request.method == "GET":
        users = User.objects.exclude(id=request.session.get('user_id'))
        return render(request, "invite_user.html", {"room": room, "users": users})

    if request.method == "POST":
        receiver_username = request.POST.get("receiver_username")

        receiver = get_object_or_404(User, username=receiver_username)

        if Invitation.objects.filter(sender=user, receiver=receiver, room=room, status="pending").exists():
            return render(request, "invite_user.html", {
                "room": room,
                "users": User.objects.exclude(id=request.session.get('user_id')),
                "error": "Invitation déjà envoyée!"
            })

        Invitation.objects.create(sender=user, receiver=receiver, room=room)
        return redirect("room_list")


@login_required
def manage_invitation_view(request, invitation_id):
    user = User.objects.get(id=request.session.get('user_id'))
    invitation = get_object_or_404(Invitation, id=invitation_id, receiver=user)

    if request.method == "GET":
        return render(request, "manage_invitation.html", {"invitation": invitation})

    if request.method == "POST":
        response = request.POST.get("response")
        if response == "accept":
            invitation.status = "accepted"
            invitation.save()
            invitation.room.members.add(user)
            UserStatus.objects.create(user=user, room=invitation.room, status="user")
        elif response == "decline":
            invitation.status = "declined"
            invitation.save()
        return redirect("invitations_list")


@login_required
def invitations_list_view(request):
    user = User.objects.get(id=request.session.get('user_id'))
    invitations = Invitation.objects.filter(receiver=user, status="pending")
    return render(request, "invitations_list.html", {"invitations": invitations})
