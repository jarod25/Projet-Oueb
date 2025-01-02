from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if "user_id" not in request.session:
            messages.error(request, "Vous devez être connecté pour accéder à cette page.")
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper
