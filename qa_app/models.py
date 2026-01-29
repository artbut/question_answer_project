from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
import os


def question_file_path(instance, filename):
    """Генерирует путь для файлов вопросов"""
    return f'questions/question_{instance.question.id}/{filename}'


def answer_file_path(instance, filename):
    """Генерирует путь для файлов ответов"""
    return f'answers/question_{instance.question.id}/{filename}'


class Category(models.Model):
    """Категория вопросов"""
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('qa_app:category_questions', kwargs={'slug': self.slug})


class Question(models.Model):
    """Вопрос"""
    title = models.CharField(max_length=200, verbose_name="Заголовок вопроса")
    content = models.TextField(verbose_name="Содержание вопроса")
    answer = models.TextField(verbose_name="Ответ", blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Категория"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Автор"
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Теги (через запятую)",
        help_text="Введите теги через запятую"
    )
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('qa_app:question_detail', kwargs={'pk': self.pk})

    def increment_views(self):
        """Увеличивает счетчик просмотров"""
        self.views += 1
        self.save(update_fields=['views'])

    def get_tags_list(self):
        """Возвращает список тегов"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []

    def has_answer(self):
        """Проверяет, есть ли ответ"""
        return bool(self.answer.strip())

    def get_files(self):
        """Возвращает все файлы вопроса"""
        return self.files.all()  # Используем related_name='files'

    def get_answer_files(self):
        """Возвращает файлы ответа"""
        return self.answer_files.all()  # Используем related_name='answer_files'


class QuestionFile(models.Model):
    """Файл, прикрепленный к вопросу"""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name="Вопрос"
    )
    file = models.FileField(
        upload_to=question_file_path,
        verbose_name="Файл"
    )
    name = models.CharField(max_length=255, verbose_name="Название файла", blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Файл вопроса"
        verbose_name_plural = "Файлы вопросов"
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.name or os.path.basename(self.file.name)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    def get_file_icon(self):
        """Возвращает иконку в зависимости от типа файла"""
        ext = os.path.splitext(self.file.name)[1].lower()
        icons = {
            '.pdf': 'fas fa-file-pdf',
            '.doc': 'fas fa-file-word',
            '.docx': 'fas fa-file-word',
            '.txt': 'fas fa-file-alt',
            '.jpg': 'fas fa-file-image',
            '.jpeg': 'fas fa-file-image',
            '.png': 'fas fa-file-image',
            '.gif': 'fas fa-file-image',
            '.zip': 'fas fa-file-archive',
            '.rar': 'fas fa-file-archive',
            '.xls': 'fas fa-file-excel',
            '.xlsx': 'fas fa-file-excel',
            '.ppt': 'fas fa-file-powerpoint',
            '.pptx': 'fas fa-file-powerpoint',
        }
        return icons.get(ext, 'fas fa-file')

    def get_file_size(self):
        """Возвращает размер файла в читаемом формате"""
        try:
            size = self.file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except (ValueError, OSError):
            return "Неизвестно"


class AnswerFile(models.Model):
    """Файл, прикрепленный к ответу"""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answer_files',
        verbose_name="Вопрос"
    )
    file = models.FileField(
        upload_to=answer_file_path,
        verbose_name="Файл"
    )
    name = models.CharField(max_length=255, verbose_name="Название файла", blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Загрузил"
    )

    class Meta:
        verbose_name = "Файл ответа"
        verbose_name_plural = "Файлы ответов"
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.name or os.path.basename(self.file.name)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    def get_file_icon(self):
        """Возвращает иконку в зависимости от типа файла"""
        ext = os.path.splitext(self.file.name)[1].lower()
        icons = {
            '.pdf': 'fas fa-file-pdf text-danger',
            '.doc': 'fas fa-file-word text-primary',
            '.docx': 'fas fa-file-word text-primary',
            '.txt': 'fas fa-file-alt text-secondary',
            '.jpg': 'fas fa-file-image text-success',
            '.jpeg': 'fas fa-file-image text-success',
            '.png': 'fas fa-file-image text-success',
            '.gif': 'fas fa-file-image text-success',
            '.zip': 'fas fa-file-archive text-warning',
            '.rar': 'fas fa-file-archive text-warning',
            '.xls': 'fas fa-file-excel text-success',
            '.xlsx': 'fas fa-file-excel text-success',
            '.ppt': 'fas fa-file-powerpoint text-danger',
            '.pptx': 'fas fa-file-powerpoint text-danger',
        }
        return icons.get(ext, 'fas fa-file text-muted')

    def get_file_size(self):
        """Возвращает размер файла в читаемом формате"""
        try:
            size = self.file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except (ValueError, OSError):
            return "Неизвестно"