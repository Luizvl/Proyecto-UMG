from django.shortcuts import render


def inicio(request):
    return render(request, "paginas/inicio.html")


def como_funciona(request):
    return render(request, "paginas/como_funciona.html")
