from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from user.models import User
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Room, Invitation, UserStatus, Message
from user import login_required
from django.utils.timezone import now, make_aware, is_naive
from datetime import date, timedelta, datetime
from django.contrib import messages
from time import sleep


@login_required
def room_list_view(request):
    user_id = request.session.get('user_id')
    user = User.objects.get(id=user_id)

    rooms = Room.objects.filter(members=user)
    rooms_with_owner = []
    for room in rooms:
        owner_status = UserStatus.objects.filter(room=room, status="owner").first()
        owner = owner_status.user if owner_status else None
        rooms_with_owner.append({"room": room, "owner": owner})

    return render(request, "room_list.html", {"rooms": rooms_with_owner})


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
    user = User.objects.get(id=request.session.get('user_id'))
    user_status = UserStatus.objects.filter(user=user, room=room_id, status="owner")
    if not user_status:
        messages.error(request, "Vous n'êtes pas autorisé à effectuer cette action.")
        return redirect("room_list")
    room = get_object_or_404(Room, id=room_id)
    room.delete()
    messages.success(request, "Le salon a été supprimé avec succès.")
    return redirect("room_list")


@login_required
def room_detail_view(request, room_id):
    user = User.objects.get(id=request.session.get('user_id'))

    if not Room.objects.filter(id=room_id, members=user).exists():
        return redirect("room_list")

    room = get_object_or_404(Room, id=room_id)

    user_status = UserStatus.objects.filter(user=user, room=room, status="banned").first()
    if user_status:
        messages.error(request, "Vous avez été banni de ce salon. Vous ne pouvez donc pas le rejoindre.")
        return redirect("room_list")

    rooms = Room.objects.filter(members=user)

    rooms_with_owner = [
        {
            "room": r,
            "owner": UserStatus.objects.filter(room=r, status="owner").first().user
            if UserStatus.objects.filter(room=r, status="owner").exists()
            else None
        }
        for r in rooms
    ]

    room_users = UserStatus.objects.filter(room=room)
    room_messages = room.messages.order_by("sent_at", "id")

    is_owner = UserStatus.objects.filter(room=room, user=user, status="owner").exists()
    is_admin = UserStatus.objects.filter(room=room, user=user, status="administrator").exists()

    return render(request, "room_details.html", {
        "room": room,
        "room_messages": room_messages,
        "rooms": rooms_with_owner,
        "today": now(),
        "yesterday": now().date() - timedelta(days=1),
        "room_users": room_users,
        "is_owner": is_owner,
        "is_admin": is_admin,
    })


last_message_times = {}


@login_required
def get_messages(request, room_id):
    user_id = request.session.get('user_id')
    user = User.objects.get(id=user_id)
    room = get_object_or_404(Room, id=room_id)
    today = date.today()
    yesterday = today - timedelta(days=1)

    is_owner = UserStatus.objects.filter(room=room, user=user_id, status="owner").exists()
    is_admin = UserStatus.objects.filter(room=room, user=user_id, status="administrator").exists()

    if not room.members.filter(id=user_id).exists():
        return JsonResponse({"error": "Unauthorized"}, status=403)

    last_seen_time = request.GET.get("last_message_time")
    if last_seen_time:
        last_seen_time = datetime.fromisoformat(last_seen_time)
        if is_naive(last_seen_time):
            last_seen_time = make_aware(last_seen_time)
    else:
        last_seen_time = now()

    timeout = 30
    start_time = now()
    while (now() - start_time).seconds < timeout:
        new_messages = room.messages.filter(
            updated_at__gt=last_seen_time
        ).order_by("sent_at")

        if new_messages.exists():
            latest_message_time = new_messages.last().updated_at.isoformat()

            messages_data = []
            for msg in new_messages:
                html_message = render_to_string('partials/message_line.html', {
                    'message': msg,
                    'today': today,
                    'yesterday': yesterday,
                    "is_owner": is_owner,
                    "is_admin": is_admin,
                    "current_user": user,
                }).strip()

                messages_data.append({
                    'id': msg.id,
                    'html': html_message,
                    'is_deleted': msg.is_deleted,
                })

            return JsonResponse({
                'messages': messages_data,
                'latest_message_time': latest_message_time,
            })

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
    if (
            room.members.filter(id=user.id).exists()
            and UserStatus.objects.filter(user=user, room=room).exists()
            and UserStatus.objects.get(user=user, room=room).status != "owner"
    ):
        room.members.remove(user)
        UserStatus.objects.get(user=user, room=room).delete()
        return redirect("room_list")
    return redirect("room_list")


@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    room = message.room
    current_user = get_object_or_404(User, id=request.session.get('user_id'))

    owner = UserStatus.objects.filter(room=room, status="owner").first()
    admins = UserStatus.objects.filter(room=room, status="administrator").values_list('user', flat=True)

    is_owner = owner and owner.user == current_user
    is_admin = current_user.id in admins
    is_author = message.author == current_user

    if not (is_owner or is_admin or is_author):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    message.is_deleted = True
    message.updated_at = now()
    message.save()

    sleep(1)
    message.delete()

    return JsonResponse({"status": "ok"})


@login_required
def edit_message(request, message_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method."}, status=405)

    message = get_object_or_404(Message, id=message_id)
    if message.author.id != request.session.get('user_id'):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    new_content = request.POST.get("content", "").strip()
    if not new_content:
        return JsonResponse({"error": "Message content cannot be empty."}, status=400)

    message.content = new_content
    message.updated_at = now()
    message.save()

    return JsonResponse({"content": message.content})
