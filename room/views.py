from user.models import User
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Room, Invitation, Status, UserStatus
from user import login_required


@login_required
def room_list_view(request):
    all_rooms = Room.objects.all()
    return render(request, "room_list.html", {"rooms": all_rooms})


@login_required
def create_room_view(request):
    if request.method == "POST":
        # Récupérer le nom du salon à partir du formulaire
        room_name = request.POST.get("name")

        # Vérifier si un salon avec le même nom existe déjà
        if Room.objects.filter(name=room_name).exists():
            return render(request, "create_room.html", {
                "error": "Un salon avec ce nom existe déjà."
            })

        # Créer le salon
        room = Room.objects.create(name=room_name)

        # Ajouter l'utilisateur comme membre du salon
        room.members.add(request.user)

        # Définir l'utilisateur comme propriétaire (owner) avec le modèle UserStatus
        from .models import Status, UserStatus
        owner_status = Status.objects.get(label="owner")  # Récupérer le statut "owner"
        UserStatus.objects.create(user=request.user, room=room, status=owner_status)

        # Rediriger vers la liste des salons après création
        return redirect("room_list")

    # Afficher la page de création de salon pour les requêtes GET
    return render(request, "create_room.html")


def search_users(request):
    query = request.GET.get('q', '')
    users = User.objects.filter(username__icontains=query)
    results = [user.username for user in users]
    return JsonResponse(results, safe=False)


@login_required
def invite_user_view(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if request.method == "GET":
        users = User.objects.exclude(id=request.user.id)
        return render(request, "invite_user.html", {"room": room, "users": users})

    if request.method == "POST":
        receiver_username = request.POST.get("receiver_username")

        receiver = get_object_or_404(User, username=receiver_username)

        if Invitation.objects.filter(sender=request.user, receiver=receiver, room=room, status="pending").exists():
            return render(request, "invite_user.html", {
                "room": room,
                "users": User.objects.exclude(id=request.user.id),
                "error": "Invitation déjà envoyée!"
            })

        Invitation.objects.create(sender=request.user, receiver=receiver, room=room)
        return redirect("room_list")


@login_required
def manage_invitation_view(request, invitation_id):
    invitation = get_object_or_404(Invitation, id=invitation_id, receiver=request.user)

    if request.method == "GET":
        return render(request, "manage_invitation.html", {"invitation": invitation})

    if request.method == "POST":
        response = request.POST.get("response")
        if response == "accept":
            invitation.status = "accepted"
            invitation.save()
            invitation.room.members.add(request.user)
        elif response == "decline":
            invitation.status = "declined"
            invitation.save()
        return redirect("invitations_list")


@login_required
def invitations_list_view(request):
    invitations = Invitation.objects.filter(receiver=request.user, status="pending")
    return render(request, "invitations_list.html", {"invitations": invitations})
