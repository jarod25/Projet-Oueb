from django.views.decorators.csrf import csrf_exempt
from user.models import User
from django.http import JsonResponse
from django.utils.html import format_html
from django.shortcuts import render, get_object_or_404, redirect
from .models import Room, Invitation, UserStatus, Message
from user import login_required
from django.utils.timezone import now
from datetime import date, timedelta
from django.contrib import messages
from time import sleep


@login_required
def room_list_view(request):
    user_id = request.session.get('user_id')
    user = User.objects.get(id=user_id)

    # Filtrer les salons où l'utilisateur est membre
    rooms = Room.objects.filter(members=user)

    return render(request, "room_list.html", {"rooms": rooms})


@login_required
def create_room_view(request):
    user = User.objects.get(id=request.session.get('user_id'))

    if request.method == "GET":
        # Renvoie uniquement le formulaire dans une modal
        return render(request, "partials/create_room_modal.html")

    if request.method == "POST":
        # Récupérer le nom du salon à partir du formulaire
        room_name = request.POST.get("name")

        # Vérifier si un salon avec le même nom existe déjà
        if Room.objects.filter(name=room_name).exists():
            return JsonResponse({"error": "Un salon avec le même nom existe déjà."}, status=400)

        # Créer le salon
        room = Room.objects.create(name=room_name)

        # Ajouter l'utilisateur comme membre du salon
        room.members.add(user)

        # Définir l'utilisateur comme propriétaire (owner) avec le modèle UserStatus
        UserStatus.objects.create(user=user, room=room, status="owner")

        # Renvoie une réponse JSON indiquant la réussite
        return redirect("room_detail", room.id)

    # Si la méthode n'est pas supportée, renvoie une erreur
    return JsonResponse({"error": "Méthode non autorisée."}, status=405)


@login_required
def delete_room_view(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    user = User.objects.get(id=request.session.get('user_id'))
    user_status = UserStatus.objects.get(room=room, user=user)
    if user_status.status != "owner":
        messages.error(request, "Vous n'êtes pas autorisé.e à effectuer cette action.")
        return redirect("room_detail", room_id=room.id)
    room.delete()
    messages.success(request, "Le salon a été supprimé avec succès.")
    return redirect("room_list")


@login_required
def room_detail_view(request, room_id):
    user = User.objects.get(id=request.session.get('user_id'))
    room = get_object_or_404(Room, id=room_id)
    user_status = UserStatus.objects.get(room=room, user=user)
    if user_status.status == "banned":
        messages.error(request, "Vous avez été banni de ce salon.")
        return redirect("room_list") 
    if not Room.objects.filter(id=room_id, members=user).exists():
        return redirect("room_list")
    rooms = Room.objects.filter(members=user)
    rooms_with_owner = []
    for owner_room in rooms:
        owner_status = UserStatus.objects.filter(room=owner_room, status="owner").first()
        owner = owner_status.user if owner_status else None
        rooms_with_owner.append({"room": owner_room, "owner": owner})
    room_users = UserStatus.objects.filter(room=room)
    room_messages = room.messages.order_by("sent_at", "id")
    return render(request, "room_details.html", {
        "room": room,
        "room_messages": room_messages,
        "rooms": rooms_with_owner,
        "today": now(),
        "yesterday": now().date() - timedelta(days=1),
        "room_users": room_users
    })


def format_message_date(sent_at):
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
                    <div class="mb-3 rounded" id="message-line" data-message-id="{id}">
                        <p class="mb-1">
                            <strong>{author}</strong>
                            <span class="small fst-italic">
                                {date}
                            </span>
                            <button type="button" title="Supprimer" id="delete-message" class="action-message px-1">
                                <i class="bi bi-trash-fill"></i>
                            </button>
                            <button type="button" title="Modifier" id="edit-message" class="action-message px-1">
                                <i class="bi bi-pencil-fill"></i>
                            </button>
                        </p>
                        <p class="text-break">{content}</p>
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
    query = request.GET.get('q', '')
    if query:
        users = User.objects.exclude(id=user.id).exclude(rooms=room_id).filter(username__icontains=query)
        matching_users = [{'id': user.id, 'username': user.username} for user in users]
        return JsonResponse(matching_users, safe=False)
    return JsonResponse({"error": "Error while searching users"}, safe=False)


@login_required
def invite_user_view(request, room_id):
    user = User.objects.get(id=request.session.get('user_id'))
    room = get_object_or_404(Room, id=room_id)

    if request.method == "GET":
        invited_users = Invitation.objects.filter(room=room, status__in=['pending', 'accepted']).values_list('receiver',
                                                                                                             flat=True)
        users = User.objects.exclude(id=user.id).exclude(id__in=invited_users)
        return render(request, "partials/invite_user_popover.html", {"room": room, "users": users})

    if request.method == "POST":
        receiver_id = request.POST.get("receiver_id")

        if receiver_id:
            receiver = get_object_or_404(User, id=receiver_id)
        else:
            return JsonResponse({"error": "Le destinataire n'est pas spécifié."}, status=400)

        if Invitation.objects.filter(sender=user, receiver=receiver, room=room, status="pending").exists():
            return JsonResponse({"error": "Invitation déjà envoyée !"}, status=400)

        Invitation.objects.create(sender=user, receiver=receiver, room=room)
        return JsonResponse({"message": "Invitation envoyée avec succès."}, status=201)

    return JsonResponse({"error": "Méthode non autorisée."}, status=405)


@csrf_exempt
@login_required
def respond_to_invitation_view(request):
    user = User.objects.get(id=request.session.get('user_id'))
    if request.method == "POST":
        try:
            invitation_id = request.POST.get("invitation_id")
            response = request.POST.get("response")
            invitation = Invitation.objects.get(id=invitation_id, receiver=user)
            if response == "accept":
                invitation.status = "accepted"
                invitation.save()
                invitation.room.members.add(user)
                UserStatus.objects.create(user=user, room=invitation.room, status="user")
                return JsonResponse({"success": True, "message": "Invitation acceptée."})
            elif response == "decline":
                invitation.delete()
                return JsonResponse({"success": True, "message": "Invitation déclinée."})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Méthode non autorisée."})


@login_required
def invitation_popover_view(request):
    user = User.objects.get(id=request.session.get('user_id'))
    invitations = Invitation.objects.filter(receiver=user, status="pending")
    return render(request, "partials/manage_invitation_popover.html", {"invitations": invitations})


@login_required
def user_role_popover(request, room_id):
    roles = UserStatus._meta.get_field('status').choices
    return render(request, "partials/user_role_popover.html", {"roles": roles})


@login_required
def update_user_role(request, room_id):
    user = User.objects.get(id=request.session.get('user_id'))
    room = get_object_or_404(Room, id=room_id)
    user_status = UserStatus.objects.get(user=user, room=room)

    if not room.members.filter(id=user.id).exists():
        return JsonResponse({"error": "Vous n'êtes pas membre de ce salon."}, status=401)

    if not UserStatus.objects.filter(user=user, room=room, status="owner").exists():
        return JsonResponse({"error": "Vous n'êtes pas autorisé à effectuer cette action."}, status=403)

    if request.method == "POST":
        new_status = request.POST.get("role")
        user_to_update_id = request.POST.get("user_id")
        user_to_update = get_object_or_404(User, id=user_to_update_id)
        mute_duration = request.POST.get("mute_duration", None)
        user_to_update_status = UserStatus.objects.get(user=user_to_update, room=room)
        if not new_status:
            return JsonResponse({"error": "Le nouveau statut n'est pas spécifié."}, status=400)
        if new_status not in dict(UserStatus._meta.get_field('status').flatchoices):
            return JsonResponse({"error": "Statut invalide."}, status=400)
        if user_to_update_status.status == "owner":
            return JsonResponse({"error": "Vous ne pouvez pas modifier le statut du propriétaire."}, status=403)
        if user_status.status == "administrator" and user_to_update_status.status == "owner":
            return JsonResponse({"error": "Vous n'êtes pas autorisé.e à effectuer cette action."}, status=403)
        if new_status not in dict(UserStatus._meta.get_field('status').flatchoices).keys():
            return JsonResponse({"error": "Statut invalide."}, status=400)
        if request.POST.get("action") == "mute":
            if not mute_duration:
                return JsonResponse({"error": "Veuillez indiquer la durée du mute."}, status=400)
            UserStatus.objects.update_or_create(user=user_to_update, room=room, defaults={"status": new_status, "mute_end_time": now() + timedelta(minutes=int(mute_duration))})
            return JsonResponse({"message": "Utilisateur réduit au silence avec succès."}, status=200)
        elif request.POST.get("action") == "unmute":
            if user_to_update_status.status == "muted":
                UserStatus.objects.update_or_create(user=user_to_update, room=room, defaults={"status": "user", "mute_end_time": None})
                return JsonResponse({"message": "Utilisateur rétabli avec succès."}, status=200)
            return JsonResponse({"error": "L'utilisateur n'est pas muet."}, status=400)
        elif request.POST.get("action") == "ban":
            UserStatus.objects.update_or_create(user=user_to_update, room=room, defaults={"status": new_status})
            return JsonResponse({"message": "Utilisateur banni avec succès."}, status=200)
        elif request.POST.get("action") == "unban":
            if user_to_update_status.status == "banned":
                UserStatus.objects.update_or_create(user=user_to_update, room=room, defaults={"status": "user"})
                return JsonResponse({"message": "Utilisateur débanni avec succès."}, status=200)
            return JsonResponse({"error": "L'utilisateur n'est pas banni."}, status=400)
        elif request.POST.get("action") == "promote":
            if user_status.status == "owner" or user_status.status == "administrator":
                if user_to_update_status.status == "user":
                    UserStatus.objects.update_or_create(user=user_to_update, room=room, defaults={"status": "administrator"})
                    return JsonResponse({"message": "Utilisateur promu avec succès."}, status=200)
                elif user_to_update_status.status == "administrator":
                    return JsonResponse({"error": "L'utilisateur est déjà administrateur."}, status=400)
                elif user_to_update_status.status == "banned" or user_to_update_status.status == "muted":
                    return JsonResponse({"error": "L'utilisateur est banni ou muet."}, status=400)
            return JsonResponse({"error": "Vous n'êtes pas autorisé.e à effectuer cette action."}, status=403)
        elif request.POST.get("action") == "demote":
            if user_status.status == "owner" or user_status.status == "administrator":
                if user_to_update_status.status == "administrator":
                    UserStatus.objects.update_or_create(user=user_to_update, room=room, defaults={"status": "user"})
                    return JsonResponse({"message": "Utilisateur rétrogradé avec succès."}, status=200)
                elif user_to_update_status.status == "user":
                    return JsonResponse({"error": "L'utilisateur est déjà utilisateur."}, status=400)
                elif user_to_update_status.status == "banned" or user_to_update_status.status == "muted":
                    return JsonResponse({"error": "L'utilisateur est banni ou muet."}, status=400)
            return JsonResponse({"error": "Vous n'êtes pas autorisé.e à effectuer cette action."}, status=403)
        return JsonResponse({"error": "Action non reconnue."}, status=400)
    return JsonResponse({"error": "Méthode non autorisée."}, status=405)

@login_required
def leave_room_view(request, room_id):
    user = User.objects.get(id=request.session.get('user_id'))
    room = get_object_or_404(Room, id=room_id)
    if room.members.filter(id=user.id).exists() and UserStatus.objects.filter(user=user, room=room).exists() and UserStatus.objects.get(user=user, room=room).status != "owner":
        room.members.remove(user)
        UserStatus.objects.get(user=user, room=room).delete()
        return redirect("room_list")
    return redirect("room_list")

@login_required
def update_user_status(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    user = User.objects.get(id=request.session.get('user_id'))
    user_status = UserStatus.objects.get(room=room, user=user)
    if user_status.status not in ["owner", "administrator"]:
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
    elif user_status.status == "owner":
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