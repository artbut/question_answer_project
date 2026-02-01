from django import forms
from django.utils.html import strip_tags

from .models import Question, Category, Tag, AttachedFile
from django.core.exceptions import ValidationError
import os


class MultipleFileInput(forms.FileInput):
    input_type = 'file'

    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs is None or 'multiple' not in attrs:
            self.attrs['multiple'] = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class QuestionForm(forms.ModelForm):
    attachments = MultipleFileField(
        required=False,
        label='Прикрепить файлы',
        help_text='Можно выбрать несколько файлов. Максимальный размер каждого файла: 10MB.'
    )

    class Meta:
        model = Question
        fields = ['title', 'content', 'category', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Теги через запятую'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) < 5:
            raise ValidationError('Заголовок должен содержать не менее 5 символов.')
        return title.strip()

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if content and len(content.strip()) < 20:
            raise ValidationError('Описание должно содержать не менее 20 символов.')
        return content

    def clean_attachments(self):
        files = self.cleaned_data.get('attachments')  # Может быть None, список или один файл

        # Если нет файлов — вернём пустой список
        if not files:
            return []

        # Приводим к списку
        if not isinstance(files, list):
            files = [files]

        # Теперь можно безопасно проверять длину
        if len(files) > 5:
            raise ValidationError('Можно прикрепить не более 5 файлов.')

        allowed_extensions = [
            '.pdf', '.doc', '.docx', '.txt',
            '.jpg', '.jpeg', '.png', '.gif',
            '.zip', '.xls', '.xlsx', '.ppt', '.pptx'
        ]
        max_file_size = 10 * 1024 * 1024  # 10 MB

        cleaned_files = []
        for file in files:
            if file:
                ext = os.path.splitext(file.name)[1].lower()
                if ext not in allowed_extensions:
                    raise ValidationError(f'Файл "{file.name}" имеет недопустимое расширение.')

                if file.size > max_file_size:
                    raise ValidationError(f'Файл "{file.name}" слишком большой. Максимум: 10MB.')

                cleaned_files.append(file)

        return cleaned_files

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()
            # Теги
            instance.tags.clear()
            tags_str = self.cleaned_data.get('tags', '')
            if tags_str:
                tag_names = [name.strip().lower() for name in tags_str.split(',') if name.strip()]
                for name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=name)
                    instance.tags.add(tag)

            # Файлы
            attachments = self.cleaned_data.get('attachments', [])
            for file in attachments:
                AttachedFile.objects.create(
                    content_object=instance,
                    file=file,
                    uploaded_by=instance.author
                )

        return instance


class AnswerForm(forms.Form):
    answer = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Введите ответ...'
        }),
        label='Ответ',
        required=True
    )

    attachments = MultipleFileField(
        required=False,
        label='Прикрепить файлы к ответу',
        help_text='Можно выбрать несколько файлов. Максимальный размер: 10MB.'
    )

    def clean_answer(self):
        answer = self.cleaned_data.get('answer')
        clean_text = strip_tags(answer).strip() if answer else ''
        if len(clean_text) < 10:
            raise ValidationError('Ответ должен содержать не менее 10 символов.')
        return answer

    def clean_attachments(self):
        files = self.cleaned_data.get('attachments', [])
        cleaned_files = []

        if files and not isinstance(files, list):
            files = [files]

        allowed_extensions = ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.gif', '.zip']
        max_file_size = 10 * 1024 * 1024  # 10 MB

        if len(files) > 5:
            raise ValidationError('Можно прикрепить не более 5 файлов.')

        for file in files:
            if file:
                ext = os.path.splitext(file.name)[1].lower()
                if ext not in allowed_extensions:
                    raise ValidationError(f'Файл "{file.name}" имеет недопустимое расширение.')
                if file.size > max_file_size:
                    raise ValidationError(f'Файл "{file.name}" слишком большой. Максимум: 10MB.')
                cleaned_files.append(file)

        return cleaned_files


# ----------------------------
# Форма поиска
# ----------------------------

class SearchForm(forms.Form):
    query = forms.CharField(
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите поисковый запрос...',
            'autofocus': 'autofocus'
        }),
        max_length=200,
        required=False
    )
    search_in = forms.ChoiceField(
        label='Где искать',
        choices=[
            ('all', 'Везде'),
            ('title', 'В заголовке'),
            ('content', 'В описании'),
            ('answer', 'В ответе'),
            ('tags', 'В тегах'),
            ('files', 'В названиях файлов'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    def clean_query(self):
        query = self.cleaned_data.get('query', '').strip()
        if query and len(query) < 2:
            raise ValidationError('Поисковой запрос должен содержать не менее 2 символов.')
        return query


# ----------------------------
# Форма входа (кастомная)
# ----------------------------

class LoginForm(forms.Form):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Проверим, существует ли пользователь
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            if user is None:
                raise ValidationError('Неверное имя пользователя или пароль.')
            elif not user.is_active:
                raise ValidationError('Аккаунт отключен.')

        return cleaned_data