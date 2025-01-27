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

    rooms = UserStatus.objects.filter(user=user).values_list("room", flat=True)
    rooms_with_owner = []
    for room_id in rooms:
        room_owner = Room.objects.get(id=room_id)
        owner_status = UserStatus.objects.filter(room=room_owner, status="owner").first()
        owner = owner_status.user if owner_status else None
        rooms_with_owner.append({"room": room_owner, "owner": owner})

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
    room = get_object_or_404(Room, id=room_id)
    check_user_to_unmute(room, user)

    user_status = get_object_or_404(UserStatus, user=user, room=room)
    if user_status.status == "banned":
        messages.error(request, "Vous avez été banni de ce salon. Vous ne pouvez donc pas le rejoindre.")
        return redirect("room_list")

    if not Room.objects.filter(id=room_id, members=user).exists():
        return redirect("room_list")

    rooms = UserStatus.objects.filter(user=user).values_list("room", flat=True)
    rooms_with_owner = []
    for room_id in rooms:
        room_owner = Room.objects.get(id=room_id)
        owner_status = UserStatus.objects.filter(room=room_owner, status="owner").first()
        owner = owner_status.user if owner_status else None
        rooms_with_owner.append({"room": room_owner, "owner": owner})

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


def check_user_to_unmute(room, user):
    user_status = get_object_or_404(UserStatus, user=user, room=room)
    if user_status.status == "muted" and user_status.mute_end_time < now():
        user_status.status = "user"
        user_status.mute_end_time = None
        user_status.save()


last_message_times = {}


@login_required
def get_messages(request, room_id):
    user_id = request.session.get('user_id')
    user = User.objects.get(id=user_id)
    room = get_object_or_404(Room, id=room_id)
    today = date.today()
    yesterday = today - timedelta(days=1)
    user_status = get_object_or_404(UserStatus, user=user, room=room)
    if user_status.status == "banned":
        return JsonResponse({"error": "Vous avez été banni de ce salon. Vous ne pouvez donc pas le rejoindre."},
                            status=403)
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
        check_user_to_unmute(room, user)

        response = process_messages(room, user, last_seen_time, today, yesterday, is_owner, is_admin)
        if response:
            return response
        sleep(1)

    return JsonResponse({'html_message': None})


def process_messages(room, user, last_seen_time, today, yesterday, is_owner, is_admin):
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

    return None


@login_required
def send_message(request, room_id):
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée."}, status=405)

    user = User.objects.get(id=request.session.get('user_id'))
    room = get_object_or_404(Room, id=room_id)
    user_status = get_object_or_404(UserStatus, user=user, room=room)
    if user_status.status == "banned":
        return JsonResponse({"error": "Vous avez été banni de ce salon. Vous ne pouvez donc pas le rejoindre."},
                            status=403)
    if user_status.status == "muted":
        return JsonResponse(
            {"error": "Vous avez été réduit au silence dans ce salon. Vous ne pouvez donc pas envoyer de message."},
            status=403)
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
    room = get_object_or_404(Room, id=room_id)
    user_status = get_object_or_404(UserStatus, user=user, room=room)
    if user_status.status == "banned":
        return JsonResponse({"error": "Vous avez été banni de ce salon. Vous ne pouvez donc pas le rejoindre."},
                            status=403)
    if user_status.status == "muted":
        return JsonResponse(
            {"error": "Vous avez été réduit au silence dans ce salon. Vous ne pouvez donc pas envoyer de message."},
            status=403)
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
    user_status = get_object_or_404(UserStatus, user=user, room=room)
    if user_status.status == "banned":
        return JsonResponse({"error": "Vous avez été banni de ce salon. Vous ne pouvez donc pas le rejoindre."},
                            status=403)
    if user_status.status == "muted":
        return JsonResponse(
            {"error": "Vous avez été réduit au silence dans ce salon. Vous ne pouvez donc pas envoyer de message."},
            status=403)
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
    current_user_status = get_object_or_404(UserStatus, user=request.session.get('user_id'), room_id=room_id)
    target_user_status = get_object_or_404(UserStatus, user_id=request.GET.get('user_id'), room_id=room_id)
    if current_user_status.status == "banned":
        return JsonResponse({"error": "Vous avez été banni de ce salon. Vous ne pouvez donc pas le rejoindre."},
                            status=403)
    can_act = current_user_status.status in ['owner', 'administrator']
    is_target_owner = target_user_status.status == 'owner'
    roles = UserStatus._meta.get_field('status').choices
    return render(request, "partials/user_role_popover.html",
                  {"roles": roles, "can_act": can_act, "is_target_owner": is_target_owner})


@login_required
def update_user_role(request, room_id):
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée."}, status=405)

    user = get_object_or_404(User, id=request.session.get('user_id'))
    room = get_object_or_404(Room, id=room_id)
    user_status = get_object_or_404(UserStatus, user=user, room=room)

    if not room.members.filter(id=user.id).exists():
        return JsonResponse({"error": "Vous n'êtes pas membre de ce salon."}, status=401)

    if user_status.status not in ["owner", "administrator"]:
        return JsonResponse({"error": "Vous n'avez pas les droits nécessaires pour effectuer cette action."},
                            status=403)

    action = request.POST.get("action")
    user_to_update_id = request.POST.get("user_id")
    mute_duration = request.POST.get("mute_duration")

    if not action or not user_to_update_id:
        return JsonResponse({"error": "Données manquantes dans la requête."}, status=400)

    user_to_update = get_object_or_404(User, id=user_to_update_id)
    user_to_update_status = get_object_or_404(UserStatus, user=user_to_update, room=room)

    if user_to_update_status.status == "owner":
        return JsonResponse({"error": "Vous ne pouvez pas modifier le statut du propriétaire."}, status=403)

    try:
        if action == "mute":
            if user_status.status != "administrator" and user_status.status != "owner":
                return JsonResponse(
                    {"error": "Seuls le propriétaire et les administrateurs peuvent bannir des utilisateurs."},
                    status=403)
            if not mute_duration:
                return JsonResponse({"error": "Durée de mute manquante."}, status=400)
            mute_end_time = now() + timedelta(minutes=int(mute_duration))
            user_to_update_status.status = "muted"
            user_to_update_status.mute_end_time = mute_end_time
            user_to_update_status.save()
            return JsonResponse({"message": "Utilisateur réduit au silence avec succès."}, status=200)

        elif action == "unmute":
            if user_to_update_status.status != "muted":
                return JsonResponse({"error": "L'utilisateur n'est pas actuellement réduit au silence."}, status=400)
            user_to_update_status.status = "user"
            user_to_update_status.mute_end_time = None
            user_to_update_status.save()
            return JsonResponse({"message": "Utilisateur rétabli avec succès."}, status=200)

        elif action == "ban":
            if user_status.status != "administrator" and user_status.status != "owner":
                return JsonResponse(
                    {"error": "Seuls le propriétaire et les administrateurs peuvent bannir des utilisateurs."},
                    status=403)
            user_to_update_status.status = "banned"
            user_to_update_status.save()
            room.members.remove(user_to_update)
            return JsonResponse({"message": "Utilisateur banni avec succès."}, status=200)

        elif action == "promote":
            if user_status.status != "owner":
                return JsonResponse({"error": "Seul le propriétaire peut promouvoir des utilisateurs."}, status=403)
            if user_to_update_status.status == "user":
                user_to_update_status.status = "administrator"
                user_to_update_status.save()
                return JsonResponse({"message": "Utilisateur promu avec succès."}, status=200)
            return JsonResponse({"error": "L'utilisateur ne peut pas être promu."}, status=400)

        elif action == "demote":
            if user_status.status != "owner":
                return JsonResponse({"error": "Seul le propriétaire peut rétrograder des administrateurs."}, status=403)
            if user_to_update_status.status == "administrator":
                user_to_update_status.status = "user"
                user_to_update_status.save()
                return JsonResponse({"message": "Utilisateur rétrogradé avec succès."}, status=200)
            return JsonResponse({"error": "L'utilisateur ne peut pas être rétrogradé."}, status=400)

        else:
            return JsonResponse({"error": "Action non reconnue."}, status=400)

    except Exception as e:
        return JsonResponse({"error": f"Une erreur est survenue : {str(e)}"}, status=500)


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
        Invitation.objects.filter(room=room, receiver=user).delete()
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
