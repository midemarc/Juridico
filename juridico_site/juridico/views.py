from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from django.core import serializers
from .models import *

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

def erreur404(request):
    return HttpResponseNotFound("""
    <h1>Erreur 404</h1>
    <p>Bah non, elle est pas là, la page...</p>
    """)

def resultats(request, reqid):
    """Sort la page des resultats.
    Demande que "reqid", l'id de la requête, soit envoyés à la page.
    """

    # reqcontent = getattr(request,request.method)
    # if "reqid" in reqcontent:
    #     reqid = int(reqcontent["reqid"])
    # else:
    #     return HttpResponse("""
    #     <h1>Erreur: information manquante</h1>
    #     <p>Le serveur ne peut retrouver votre requête.</p>
    #     """)

    requete = Requete.objects.get(reqid=reqid)
    directions = Direction.objects.filter(requete=requete)
    
