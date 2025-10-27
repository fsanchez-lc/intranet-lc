from django.shortcuts import render
from navigation.utils import with_menu
from django.contrib.auth.decorators import login_required

@login_required
def MenuView(request):
    return render(request, 'navigation/base.html', with_menu(request))
