from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def EmployeesView(request):
    return render(request, 'employees.html', {})
