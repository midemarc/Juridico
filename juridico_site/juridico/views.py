from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
from .models import Question

from .forms import QuestionForm


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def questions(request):
    questions = serializers.serialize('json', Question.objects.all())
    return HttpResponse(questions)


def question(request, question_id):
    question = Question.objects.filter(qid=question_id)[0]
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            return HttpResponse('coucou')
    else:
        form = QuestionForm()
    return render(
        request,
        'question.html',
        {
            'question_label': question.question,
            'form': form
        }
      )
