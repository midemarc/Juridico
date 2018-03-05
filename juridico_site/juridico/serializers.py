from rest_framework import serializers
from .models import Question


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
