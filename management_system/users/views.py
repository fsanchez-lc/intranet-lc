from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def UsersView(request):
    return render(request, 'users.html', {})
