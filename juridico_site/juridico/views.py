from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
from .models import Question

from .forms import *


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def questions(request):
    questions = serializers.serialize('json', Question.objects.all())
    return HttpResponse(questions)


def question(request, question_id):
    question = Question.objects.filter(qid=question_id)[0]
    if request.method == 'POST':
        # form = QuestionForm(request.POST)
        if question.reponse_type == "t":
            form = QuestionFormText(request.POST)
        elif question.reponse_type == "e":
            form = QuestionFormInt(request.POST)
        elif question.reponse_type == "f":
            form = QuestionFormFloat(request.POST)
        elif question.reponse_type == "b":
            form = QuestionFormBool(request.POST)
        if form.is_valid():
            return HttpResponse('coucou' + str(form.cleaned_data['reponse']))
    else:
        if question.reponse_type == "t":
            form = QuestionFormText()
        elif question.reponse_type == "e":
            form = QuestionFormInt()
        elif question.reponse_type == "f":
            form = QuestionFormFloat()
        elif question.reponse_type == "b":
            form = QuestionFormBool()

    return render(
        request,
        'question.html',
        {
            'question_id': question_id,
            'question_label': question.question,
            'form': form
        }
      )

def reponse(request):
    cid = request.GET["cid"] if request.method == "GET" else request.POST["cid"]
    reqid = request.GET["reqid"] if request.method == "GET" else request.POST["reqid"]
