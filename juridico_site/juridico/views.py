from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from django.shortcuts import render, redirect
from django.core import serializers
from typing import List
from django.views.decorators.csrf import csrf_exempt

from juridico.serializers import QuestionSerializer, ReponseSerializer, DocumentationSerializer, OrganisationSerializer
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

    return redirect("/juridico/antique/question" % prochaine_question)

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


def api_next_question(request):
    """Gets the next question after a specific answer

    :return: a serialized **models.Question** object.

    :return: A JSON object with the question id as the value of 'question_id' key if *id_only* has been passed as HTTP argument
    """
    # if request.method == 'GET':
    try:
        request_id: int = int(request.GET["reqid"])
        reponse_id: int = int(request.GET['repid'])

        if reponse_id is -1:
            # Convention pour la requete
            return JsonResponse({
                # Temporary cheat, always first question
                'question_id': 1
            })

        id_only: bool = bool(int(request.GET.get('id_only', '0')))
        o_reponse = Reponse.objects.get(repid=reponse_id)
        o_request = Requete.objects.get(reqid=request_id)
        method = getattr(met, f'question{o_reponse.question_id}')
        next_question_id = method(requete=o_request, reponse=o_reponse)

        if not next_question_id:
            return JsonResponse({})

        if next_question_id == -1:
            return JsonResponse({
                'question_id': next_question_id
            })

        o_question = Question.objects.get(qid=next_question_id)

        if id_only:
            return JsonResponse({
                'question_id': o_question.qid
            })

        serializer = QuestionSerializer(o_question)
        return JsonResponse(serializer.data)
    except AttributeError:
        raise NotImplementedError('')
    pass

@api_view(['GET', 'POST'])
def api_resultats(request):
    """Retourne les résultats. Trois types de résultats: des org"""
    try:
        request_id: int = int(request.GET["reqid"])
        req = Requete.objects.get(reqid=request_id)

        # Populer les résultats
        n_orgs = RessourceDeRequete.objects.filter(
                type_classe="Organisation",
                requete=req
                ).count()
        n_docs =RessourceDeRequete.objects.filter(
                type_classe="Documentation",
                requete=req
                ).count()

        compte_desire_docu = int(request.GET.get("compte_desire_docu",10))
        compte_desire_orgs = int(request.GET.get("compte_desire_orgs",10))

        if n_orgs < compte_desire_orgs:
            met.add_orgs(req, conditions=None, topn=compte_desire_orgs-n_orgs, poids=0.3)

        if n_docs < compte_desire_docu:
            v = req.get_desc_vector()
            for d, o in met.get_top_educaloi(v,topn=compte_desire_docu-n_docs):
                met.add_documentation(req, o.resid, poids=0.3)


        # Les convertir en json pour les envoyer à angular

        docu_objs = DocumentationSerializer(
            [
                Documentation.objects.get(resid=rr.resid)
                for rr in RessourceDeRequete.objects.filter(
                    type_classe="Documentation",
                    requete=req
                    ).order_by("-poids")
            ],
            many=True
        ).data


        orgs = [
            Organisation.objects.get(resid=rr.resid)
            for rr in RessourceDeRequete.objects.filter(
                type_classe="Organisation",
                requete=req
                ).order_by("-poids")
        ]
        orgs_avocat = [ i for i in orgs if i.tags.filter(pk=11).count() > 0 ]
        orgs_autres = [ i for i in orgs if i.tags.filter(pk=11).count() == 0 ]

        org_objs = OrganisationSerializer(
            orgs_avocat + orgs_autres,
            many=True
        ).data

        dir_objs = [
            {
                "resid": o.resid,
                "description": Direction.objects.get(resid=o.resid).formatted_description(req)
            }
            for o in RessourceDeRequete.objects.filter(
                type_classe="Direction",
                requete=req
                )
        ]

        return JsonResponse({
            "directions": dir_objs,
            "documentation": docu_objs,
            "organisations": org_objs
        })

    except AttributeError:
        raise NotImplementedError('')

    pass

def api_nouv_requete(request, cid=None):
    """
    Crée une nouvelle requête

    :return: un Json avec une entrée "requete_id" qui correspond à l'id de la
    requete crée.
    """
    dat = getattr(request, request.method)
    pcid = cid if cid != None else dat.get("cid")
    pcid = 1 if pcid == None or pcid == '' else pcid
    client = Client.objects.get(cid=int(pcid))

    req = Requete.objects.create(
        description_cas = dat.get("description_cas"),
        client = client,
        ip = get_client_ip(request)
    )
    req.save()

    return JsonResponse({
        "requete_id": req.reqid
    })

def antique_question(request, cid=None):
    dat = getattr(request, request.method)
    pcid = cid if cid != None else dat.get("cid")

    fvars = {"q0class": "q0done", "q0actif": " disabled"}

    if dat.get("reqid") != None:
        # après avoir rempli la première question
        req = Requete.objects.get(reqid=int(dat.get("reqid")))
        qnum = int(dat.get("qnum"))
        question = Question.objects.get(qid=qnum)
        fvars["requete"] = req
        reponse = Reponse.objects.create(
            requete = req,
            question = question,
            reponse = dat.get("reponse").strip()
        )
        reponse.save()

        qfn = getattr(met,"question%d" % qnum)
        next_qnum = qfn(req, reponse)

        if next_qnum == -1:
            return antique_resultats(request)

        fvars["qnum"] = next_qnum
        fvars["qactive"] = Question.objects.get(qid=next_qnum)
        fvars["reponses"] = Reponse.objects.filter(requete=req)

        return render(request, "question_ant.html", fvars)


    else:
        pcid = 1 if pcid == None or pcid == '' else pcid
        client = Client.objects.get(cid=int(pcid))
        fvars["client"] = client
        fvars["reponses"] = []

        if "description_cas" in dat:
            # Après avoir entré la description
            fvars["q0class"] = "q0done"
            req = Requete.objects.create(
                description_cas = dat.get("description_cas"),
                client = client,
                ip = get_client_ip(request)
            )
            req.save()
            fvars["requete"] = req
            next_qnum = met.desc2domaine(req.description_cas)
            fvars["qnum"] = next_qnum
            fvars["qactive"] = Question.objects.get(qid=next_qnum)
            fvars["reponses"] = []

            return render(request, "question_ant.html", fvars)

        else:
            # avant d'avoir entré la description
            client= Client.objects.get(cid=int(1))
            fvars["client"] = client
            fvars["reponses"] = []
            fvars["qnum"] = 0
            fvars["reponses"] = []
            fvars["q0actif"] = ""
            return render(request, "question_ant.html", fvars)

def antique_resultats(request, requeteid=None):
    dat = getattr(request, request.method)
    # reqid = requeteid if requeteid != None else int(dat.get("reqid"))
    reqid = int(dat.get("reqid"))
    req = Requete.objects.get(reqid=reqid)

    fvars = {"requete": req}

    # Populer les résultats
    n_orgs = RessourceDeRequete.objects.filter(
            type_classe="Organisation",
            requete=req
            ).count()
    n_docs =RessourceDeRequete.objects.filter(
            type_classe="Documentation",
            requete=req
            ).count()

    compte_desire = 10
    from juridico.methodes import get_top_educaloi, add_orgs, add_documentation

    if n_orgs < compte_desire:
        add_orgs(req, conditions=None, topn=compte_desire-n_orgs)

    if n_docs < compte_desire:
        v = req.get_desc_vector()
        for d, o in get_top_educaloi(v,topn=compte_desire-n_docs):
            add_documentation(req, o.resid)


    # Les convertir en json pour les envoyer à angular

    fvars["documentation"] = [Documentation.objects.get(resid=rr.resid)
            for rr in RessourceDeRequete.objects.filter(
                type_classe="Documentation",
                requete=req
                )]

    fvars["organisations"] = [Organisation.objects.get(resid=rr.resid)
            for rr in RessourceDeRequete.objects.filter(
                type_classe="Organisation",
                requete=req
                )]

    fvars["directions"] = [ Direction.objects.get(resid=rr.resid).formatted_description(req)
            for rr in RessourceDeRequete.objects.filter(
                type_classe="Direction",
                requete=req
            )]

    return render(request,"resultats_ant.html", fvars)
