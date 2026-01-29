from django import forms
from .models import Question, Category, QuestionFile, AnswerFile


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class QuestionForm(forms.ModelForm):
    attachments = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.zip,.rar,.xls,.xlsx,.ppt,.pptx'
        }),
        label="Прикрепить файлы",
        help_text="Можно выбрать несколько файлов (удерживайте Ctrl/Cmd для выбора нескольких). Максимальный размер каждого файла: 10MB"
    )

    class Meta:
        model = Question
        fields = ['title', 'content', 'category', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок вопроса'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Опишите ваш вопрос подробно...'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'тег1, тег2, тег3'
            }),
        }


class AnswerForm(forms.ModelForm):
    attachments = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.zip,.rar,.xls,.xlsx,.ppt,.pptx'
        }),
        label="Прикрепить файлы к ответу",
        help_text="Можно выбрать несколько файлов (удерживайте Ctrl/Cmd для выбора нескольких). Максимальный размер каждого файла: 10MB"
    )

    class Meta:
        model = Question
        fields = ['answer']
        widgets = {
            'answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Введите подробный ответ на вопрос...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['answer'].label = "Ответ"


class SearchForm(forms.Form):
    query = forms.CharField(
        label='Поиск',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите поисковый запрос...'
        })
    )
    search_in = forms.ChoiceField(
        label='Искать в',
        choices=[
            ('all', 'Везде'),
            ('title', 'В заголовках'),
            ('content', 'В содержании'),
            ('answer', 'В ответах'),
            ('tags', 'В тегах'),
            ('files', 'В названиях файлов'),
        ],
        initial='all',
        widget=forms.RadioSelect,
        required=False
    )