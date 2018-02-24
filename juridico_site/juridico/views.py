from django.http import HttpResponse
from django.shortcuts import render
#from .models import Question

from .forms import QuestionForm


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)

        if form.is_valid():
            return HttpResponse('coucou')
    else:
        form = QuestionForm()
    return render(request, 'question.html', {'form': form})
