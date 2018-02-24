from django import forms


class QuestionForm(forms.Form):
    question = forms.CharField(label='Question', max_length=100)
