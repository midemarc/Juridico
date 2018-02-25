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
    o_question = Question.objects.filter(qid=question_id)[0]
    if request.method == 'POST':
        # reqcontent = getattr(request, request.method)
        # user: Client = None
        # # TODO: get id requete
        # default_requete: Requete().save()
        # try:
        #     user_id = reqcontent['user_id']
        #     user = Client.objects.filter(cid=user_id)[0]
        # except KeyError:
        #     raise ValueError('user_id')
        default_user = Client.objects.filter(cid=1)
        default_request = Requete.objects.filter(reqid=1)


        # reqcontent.get('user_id')
        # form = QuestionForm(request.POST)
        if o_question.reponse_type == "t":
            form = QuestionFormText(request.POST)
        elif o_question.reponse_type == "e":
            form = QuestionFormInt(request.POST)
        elif o_question.reponse_type == "f":
            form = QuestionFormFloat(request.POST)
        elif o_question.reponse_type == "b":
            form = QuestionFormBool(request.POST)
        if form.is_valid():
            reponse: Reponse = Reponse()
            reponse.question = o_question
            reponse.client = default_user
            reponse.requete = default_request
            reponse.reponse = form.cleaned_data['reponse']
            reponse.save()

            # return HttpResponse('coucou' + str(form.cleaned_data['reponse']))
            return HttpResponse('coucou' + str(reponse))
    else:
        if o_question.reponse_type == "t":
            form = QuestionFormText()
        elif o_question.reponse_type == "e":
            form = QuestionFormInt()
        elif o_question.reponse_type == "f":
            form = QuestionFormFloat()
        elif o_question.reponse_type == "b":
            form = QuestionFormBool()

    return render(
        request,
        'question.html',
        {
            'question_id': question_id,
            'question_label': o_question.question,
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
    camarades = Camarade.objects.filter(requete=requete)
    organismes = Organisation.objects.filter(requete=requete)
    documentation = Documentation.objects.filter(requete=requete)

    return render(
        request,
        'resultats.html',
        {
        'directions': directions,
        'camarades': camarades,
        'documentation': documentation,
        'organismes': organismes
        }
    )
