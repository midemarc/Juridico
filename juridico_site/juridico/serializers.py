from rest_framework import serializers
from .models import Question, Reponse, Direction, Documentation, Organisation


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = (
            'qid',
            'nom',
            'question',
            'reponse_type',
            'options'
        )
        read_only_fields = (
            'options',
        )
        options = serializers.ListField(source='options')


class ReponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reponse
        fields = (
            'repid',
            'question',
            'requete',
            'reponse'
        )

class DocumentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documentation
        fields = (
            'resid',
            'nom',
            'url',
            'description',
            'source'
        )
        read_only_fields = ('source', )

class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation

        fields = (
            'resid',
            'nom',
            'url',
            'description',
            'code_postal',
            'adresse',
            'courriel',
            'telephone',
            'telecopieur',
            'heures_ouverture'
        )

class DirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = (
            'resid',
            'formatted_description'
        )
        read_only_fields = (
            'formatted_description',
        )

# class ResultatsSerializer(serializers.Serializer):
#     organisations = OrganisationSerializer(many=True)
#     directions = DirectionSerializer(many=True)
#     documentation = DocumentationSerializer(many=True)
#
#     class Meta:
#         fields =(
#             "organisations",
#             "directions",
#             "documentation"
#             )
