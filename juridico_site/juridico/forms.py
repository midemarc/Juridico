from django import forms


class QuestionFormText(forms.Form):
    reponse = forms.CharField(label='Question', max_length=100)


class QuestionFormInt(forms.Form):
    reponse = forms.IntegerField()


class QuestionFormFloat(forms.Form):
    reponse = forms.FloatField()


class QuestionFormBool(forms.Form):
    reponse = forms.BooleanField()