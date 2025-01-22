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
    room.delete()
    return redirect("room_list")


@login_required
def room_detail_view(request, room_id):
    user = User.objects.get(id=request.session.get('user_id'))
    if not Room.objects.filter(id=room_id, members=user).exists():
        return redirect("room_list")
    room = get_object_or_404(Room, id=room_id)
    rooms = Room.objects.filter(members=user)
    room_users = UserStatus.objects.filter(room=room)
    room_messages = room.messages.order_by("sent_at", "id")
    return render(request, "room_details.html", {
        "room": room,
        "room_messages": room_messages,
        "rooms": rooms,
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
        # Récupère le dernier message envoyé ou modifié
        latest_message = room.messages.order_by("-sent_at", "-updated_at").first()

        # Vérifie si le dernier message est nouveau ou a été mis à jour
        if latest_message and (latest_message.sent_at > last_message_time or latest_message.updated_at > last_message_time):
            # Met à jour le dernier temps enregistré
            last_message_times[room_id] = max(latest_message.sent_at, latest_message.updated_at)

            # Prépare les messages pour l'affichage
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

    if not room.members.filter(id=user.id).exists():
        return JsonResponse({"error": "Vous n'êtes pas membre de ce salon."}, status=401)

    if not UserStatus.objects.filter(user=user, room=room, status="owner").exists():
        return JsonResponse({"error": "Vous n'êtes pas autorisé à effectuer cette action."}, status=403)

    if request.method == "POST":
        new_status = request.POST.get("role")
        user_to_update_id = request.POST.get("user_id")
        user_to_update = get_object_or_404(User, id=user_to_update_id)
        if not new_status:
            return JsonResponse({"error": "Le nouveau statut n'est pas spécifié."}, status=400)

        if new_status not in dict(UserStatus._meta.get_field('status').flatchoices):
            return JsonResponse({"error": "Statut invalide."}, status=400)

        UserStatus.objects.update_or_create(user=user_to_update, room=room, defaults={"status": new_status})
        return JsonResponse({"message": "Statut mis à jour avec succès."}, status=200)

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
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if message.author.id != request.session.get('user_id'):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    room_id = message.room.id
    message.delete()

    # Met à jour le temps de dernière modification pour la salle
    last_message_times[room_id] = now()

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
    message.save()

    return JsonResponse({"content": message.content})