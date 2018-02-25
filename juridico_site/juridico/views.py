from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.core import serializers
from .models import *
from .methodes import *

from .forms import *


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def questions(request):
    questions = serializers.serialize('json', Question.objects.all())
    return HttpResponse(questions)

def question0(request):
    reqcontent = getattr(request,request.method)

    requete = Requete.objects.create(
        description_cas = reqcontent["description_cas"],
        client = Client.objects.get(cid=int(reqcontent["cid"]))
    )
    requete.save()

    prochaine_question = desc2domaine(reqcontent["description_cas"])

    return redirect("question%d" % prochaine_question)

def question(request, question_id):
    if question_id == 0:
        return question0(request)

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
        default_user = Client.objects.get(cid=1)
        default_request: Requete = Requete.objects.get(reqid=1)
        # default_request.client = default_user


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
        elif o_question.reponse_type == "d":
            form = QuestionFormDate()
        elif o_question.reponse_type == "l":
            form = QuestionFormDate(Question.reponse_type.all())
        else:
            raise ValueError(f'Type de réponse non  pris en compte : {o_question.reponse_type}')

        if form.is_valid():
            # reponse: Reponse = Reponse()
            # reponse.question = o_question
            # reponse.client = default_user
            # reponse.requete = default_request
            # reponse.reponse = form.cleaned_data['reponse']
            reponse = Reponse.objects.create(
                question = o_question,
                client = default_user,
                requete = default_request,
                reponse = form.cleaned_data['reponse']
            )
            reponse.save()

            next_question_id = next_question(question_id, reponse.reponse)
            print(f'next question id : {next_question_id}')

            # return HttpResponse('coucou' + str(form.cleaned_data['reponse']))
            # return HttpResponse('coucou' + str(reponse))
            return redirect(f'/juridico/question{next_question_id}')
    else:
        if o_question.reponse_type == "t":
            form = QuestionFormText()
        elif o_question.reponse_type == "e":
            form = QuestionFormInt()
        elif o_question.reponse_type == "f":
            form = QuestionFormFloat()
        elif o_question.reponse_type == "b":
            form = QuestionFormBool()
        elif o_question.reponse_type == "d":
            form = QuestionFormDate()
        elif o_question.reponse_type == "l":
            form = QuestionFormDate(Question.reponse_type.all())
        else:
            raise ValueError(f'Type de reponse non pris en compte : {o_question.reponse_type}')

    return render(
        request,
        'question.html',
        {
            'question_id': question_id,
            'question_label': o_question.question,
            'form': form
        }
      )


def next_question(question_id: int, answer: str) -> int:
#    pass
#    if question_id == 0:
    if answer:
        return 3
    else:
        return 4

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

def requete(request, cid):
    return render(
        request,
        'requete.html',
        {
        'cid': cid
        }
    )
