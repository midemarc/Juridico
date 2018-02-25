from django import forms


class QuestionFormText(forms.Form):
    reponse = forms.CharField(label='Question', max_length=100)


class QuestionFormInt(forms.Form):
    reponse = forms.IntegerField()


class QuestionFormFloat(forms.Form):
    reponse = forms.FloatField()


class QuestionFormBool(forms.Form):
    reponse = forms.BooleanField()


class QuestionFormDate(forms.Form):
    reponse = forms.DateField()


class QuestionFormList(forms.Form):
    def __init__(self, possibilities):
        reponse = forms.ModelChoiceField(
            queryset=possibilities
        )