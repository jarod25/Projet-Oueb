from user.models import User
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Room, Invitation
from user import login_required


@login_required
def room_list_view(request):
    # TODO: Get all rooms where the user is a member
    return render(request, "room_list.html", {"rooms": []})


@login_required
def create_room_view(request):
    # TODO: Create a new room with the current user as the owner
    return


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
