from user.models import User


def authentication_status(request):
    user = None
    if 'user_id' in request.session:
        try:
            user = User.objects.get(id=request.session['user_id'])
        except User.DoesNotExist:
            pass
    return {
        'is_authenticated': user is not None,
        'current_user': user,
    }
