from django.shortcuts import render

def vista_regata(request):
    # Esto buscará automáticamente el archivo en dinamicas/templates/regata.html
    return render(request, 'regata.html')