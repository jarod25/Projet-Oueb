from user.models import User
from django.http import JsonResponse
from django.utils.html import format_html
from django.shortcuts import render, get_object_or_404, redirect
from .models import Room, Invitation, UserStatus, Message
from user import login_required
from django.utils.timezone import now
from datetime import timedelta
from django.contrib import messages
from time import sleep


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
    if request.user != room.owner:
        messages.error(request, "Vous n'êtes pas autorisé.e à effectuer cette action.")
        return redirect("room_detail", room_id=room.id)
    room.delete()
    messages.success(request, "Le salon a été supprimé avec succès.")
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


last_message_times = {}


@login_required
def get_messages(request, room_id):
    user = request.session.get('user_id')
    room = get_object_or_404(Room, id=room_id)

    if not room.members.filter(id=user).exists():
        return JsonResponse({"error": "Unauthorized"}, status=403)

    last_message_time = last_message_times.get(room_id, now())

    timeout = 30
    start_time = now()
    while (now() - start_time).seconds < timeout:
        latest_message = room.messages.order_by("-sent_at").first()
        if latest_message and latest_message.sent_at > last_message_time:
            last_message_times[room_id] = latest_message.sent_at

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
            return JsonResponse({'html_message': html_message})

        sleep(1)

    return JsonResponse({'html_message': None})


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
    last_message_times[room_id] = message.sent_at
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

@login_required
def update_user_status(request, room_id, user_id):
    room = get_object_or_404(Room, id=room_id)
    user_status = get_object_or_404(UserStatus, user_id=user_id, room=room)
    # check if the user is the owner / admin of the room
    if request.user != room.owner and not room.administrator:
        messages.error(request, "Vous n'êtes pas autorisé.e à effectuer cette action.")
        return redirect("room_detail", room_id=room.id)
    action = request.POST.get("action")
    mute_duration = request.POST.get("mute_duration")
    if action == "mute":
        user_status.status = "muted"
        user_status.mute_end_time = now() + timedelta(minutes=int(mute_duration))
        messages.success(request, "L'utilisateur {user_status.user.username} a été réduit au silence pour {mute_duration} minutes.")
    elif action == "unmute":
        if user_status.status == "muted":
            user_status.status = "user"
            user_status.mute_end_time = None
            messages.success(request, "L'utilisateur {user_status.user.username} est de retour dans le chat.")
    elif action == "ban":
        user_status.status = "banned"
        messages.success(request, "L'utilisateur {user_status.user.username} a été banni.")
    elif action == "unban":
        if user_status.status == "banned":
            user_status.status = "user"
            messages.success(request, "L'utilisateur {user_status.user.username} a été débanni.")
    elif request.user == room.owner :
        if action == "promote":
            if user_status.status == "user":
                user_status.status = "administrator"
                messages.success(request, "L'utilisateur {user_status.user.username} a été promu administrateur.")
            elif user_status.status == "administrator":
                messages.error(request, "L'utilisateur {user_status.user.username} est déjà administrateur.")
        elif action == "demote":
            if user_status.status == "administrator":
                user_status.status = "user"
                messages.success(request, "L'utilisateur {user_status.user.username} n'est plus administrateur.")
    else:
        messages.error(request, "Action non reconnue.")
        return redirect("room_detail", room_id=room.id)
    user_status.save()
    return redirect("room_detail", room_id=room.id)