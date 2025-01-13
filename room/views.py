from user.models import User
from django.http import JsonResponse
from django.utils.html import format_html
from django.shortcuts import render, get_object_or_404, redirect
from .models import Room, Invitation, UserStatus, Message
from user import login_required
from django.utils.timezone import now
from datetime import timedelta
from django.contrib import messages


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
            messages.error(request, "Un salon avec le même nom existe déjà.")
            return render(request, "create_room.html")

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
    user = User.objects.get(id=request.session.get('user_id'))
    if not Room.objects.filter(id=room_id, members=user).exists():
        return redirect("room_list")
    room = get_object_or_404(Room, id=room_id)
    rooms = Room.objects.filter(members=user)

    room_messages = room.messages.order_by("sent_at", "id")
    return render(request, "room_details.html", {
        "room": room,
        "room_messages": room_messages,
        "rooms": rooms,
        "today": now(),
        "yesterday": now().date() - timedelta(days=1)
    })


def format_message_date(sent_at):
    from datetime import date, timedelta

    today = date.today()
    yesterday = today - timedelta(days=1)

    if sent_at.date() == today:
        return format_html('<span class="message-date text-muted">Aujourd\'hui à {}</span>', sent_at.strftime('%H:%M'))
    elif sent_at.date() == yesterday:
        return format_html('<span class="message-date text-muted">Hier à {}</span>', sent_at.strftime('%H:%M'))
    else:
        return format_html('<span class="message-date text-muted">Le {} à {}</span>', sent_at.strftime('%d/%m/%Y'),
                           sent_at.strftime('%H:%M'))


@login_required
def get_messages(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if not room.members.filter(id=request.session.get('user_id')).exists():
        return JsonResponse({"error": "Vous n'êtes pas membre de ce salon."}, status=401)
    room_messages = room.messages.order_by("sent_at", "id")
    html_message = ""
    for message in room_messages:
        html_message += format_html(
            """
            <div class="message mb-3" data-message-id="{id}">
                <p class="mb-1">
                    <strong>{author}</strong>
                    {date}
                </p>
                <p class="message-content">
                    {content}
                </p>
            </div>
            """,
            id=message.id,
            author=message.author.username,
            date=format_message_date(message.sent_at),
            content=message.content.replace("\n", "<br>"),
        )
    return JsonResponse({
        'html_message': html_message,
    })


@login_required
def send_message(request, room_id):
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée."}, status=405)

    user = User.objects.get(id=request.session.get('user_id'))
    room = get_object_or_404(Room, id=room_id)

    if not room.members.filter(id=user.id).exists():
        return JsonResponse({"error": "Vous n'êtes pas membre de ce salon."}, status=401)

    content = request.POST.get("content")
    if not content:
        return JsonResponse({"error": "Le contenu du message est vide."}, status=400)

    message = Message.objects.create(content=content, room=room, author=user)
    return JsonResponse(
        {"message": message.content, "author": user.username, "sent_at": message.sent_at.strftime("%d/%m/%Y %H:%M"),
         "room_id": room.id})


@login_required
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
        return redirect("room_detail", room_id=room.id)


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
