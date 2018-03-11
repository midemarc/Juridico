from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from django.shortcuts import render, redirect
from django.core import serializers
from typing import List
from django.views.decorators.csrf import csrf_exempt

from juridico.serializers import QuestionSerializer, ReponseSerializer
from .models import *
import juridico.methodes as met

from .forms import *

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def index(request):
    return redirect("requete/client1")

def questions(request):
    questions = serializers.serialize('json', Question.objects.all())
    return HttpResponse(questions)

def question0(request):
    reqcontent = getattr(request, request.method)
    # print('question0------------')
    requete = Requete.objects.create(
        description_cas = reqcontent["description_cas"],
        client = Client.objects.get(cid=int(reqcontent["cid"])),
        ip = get_client_ip(request)
    )
    requete.save()

    prochaine_question = met.desc2domaine(reqcontent["description_cas"])
    print("test question0")

    return redirect("/juridico/question%d" % prochaine_question)

def question(request, question_id):
    if question_id == 0:
        return question0(request)

    o_question = Question.objects.filter(qid=question_id)[0]
    if request.method == 'POST':
        default_user = Client.objects.get(cid=1)
        default_request = Requete.objects.get(reqid=1)

        if o_question.reponse_type == "t":
            form = QuestionFormText(request.POST)
        elif o_question.reponse_type == "e":
            form = QuestionFormInt(request.POST)
        elif o_question.reponse_type == "f":
            form = QuestionFormFloat(request.POST)
        elif o_question.reponse_type == "b":
            form = QuestionFormBool(request.POST)
        elif o_question.reponse_type == "d":
            form = QuestionFormDate(request.POST)
        elif o_question.reponse_type == "l":
            form = QuestionFormList(request.POST)
        else:
            raise ValueError('Type de réponse non  pris en compte : {o_reponse_type}'.format(
                o_reponse_type=o_question.reponse_type
            ))

        if form.is_valid():
            reponse = Reponse.objects.create(
                question = o_question,
                client = default_user,
                requete = default_request,
                reponse = form.cleaned_data['reponse']
            )
            reponse.save()

            next_question_id = next_question(question_id, reponse.reponse)
            return redirect('/juridico/question{next_question_id}'.format(
                next_question_id=next_question_id
            ))
        else:
            raise ValueError('Form not valid')
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
            elements = o_question.contenu_liste.split('\r\n')

            form = QuestionFormList()
            # form = QuestionFormList(choice_list=__list_to_tuple(elements))
            # form.response = forms.ChoiceField(choices=d)
        else:
            raise ValueError('Type de reponse non pris en compte : %s' % o_question.reponse_type)

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
    print('next question()')
#    pass
#    if question_id == 0:
    if 'Yes' in answer:
        return 6
    else:
        return 7

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


@api_view(['GET', 'POST'])
def api_questions(request):
    if request.method == 'GET':
        questions = Question.objects.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def api_question(request, question_id: int):
    """
    Retrieve, update or delete a question
    """
    try:
        question = Question.objects.get(qid=question_id)
    except Question.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = QuestionSerializer(question)
        return JsonResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = QuestionSerializer(question, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        question.delete()
        return HttpResponse(status=204)


@api_view(['GET', 'POST'])
def api_reponses(request):
    """GET lists all responses (models.Reponse serialized)

    POST creates one"""
    if request.method == 'GET':
        reponses = Reponse.objects.all()
        serializer = ReponseSerializer(reponses, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ReponseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# def api_next_question(request, request_id: int, reponse_id: int):
def api_next_question(request):
    """Gets the next question after a specific answer

    :return: a serialized **models.Question** object.
    """
    # if request.method == 'GET':
    try:
        print(f'request_id {request.GET["reqid"]}')
        reponse_id: int = int(request.GET["reqid"])
        request_id: int = int(request.POST['repid'])
        o_reponse = Reponse.objects.get(repid=reponse_id)
        o_request = Requete.objects.get(reqid=request_id)
        method = getattr(met, f'question{o_reponse.question_id}')
        return method(requete=o_request, reponse=o_reponse)
    except AttributeError:
        raise NotImplementedError('')
    pass
