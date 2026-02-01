from django.db import models
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from pathlib import Path
import os
import bleach


# ----------------------------
# Валидаторы
# ----------------------------

def validate_file_size(value):
    limit = 5 * 1024 * 1024  # 5 MB
    if value.size > limit:
        raise ValidationError('Файл слишком большой. Максимум 5 МБ.')


def validate_file_type(value):
    ext = Path(value.name).suffix.lower()
    allowed = ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', '.xls', '.xlsx', '.ppt', '.pptx']
    if ext not in allowed:
        raise ValidationError(f'Тип файла {ext} не поддерживается.')


# ----------------------------
# Теги
# ----------------------------

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название тега")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


# ----------------------------
# Категории
# ----------------------------

class Category(models.Model):
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


# ----------------------------
# Вопрос
# ----------------------------

class Question(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок вопроса")
    content = CKEditor5Field(config_name='extends', verbose_name="Содержание вопроса")
    answer = CKEditor5Field(config_name='extends', verbose_name="Ответ", blank=True)
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
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Теги")
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['title']),
            models.Index(fields=['category']),
            models.Index(fields=['is_published', '-created_at']),
            models.Index(fields=['category', 'is_published', '-created_at']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('qa_app:question_detail', kwargs={'pk': self.pk})

    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    def has_answer(self):
        if not self.answer:
            return False
        clean_text = strip_tags(self.answer).strip()
        return bool(clean_text)

    def clean(self):
        """
        Очищает HTML от потенциально опасных тегов и атрибутов.
        Вызывается в форме через full_clean().
        """
        if self.content:
            self.content = self.sanitize_html(self.content)
        if self.answer:
            self.answer = self.sanitize_html(self.answer)

    @staticmethod
    def sanitize_html(html_content):
        """
        Очищает HTML с помощью bleach.
        Разрешены только безопасные теги и атрибуты.
        """
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
            'h1', 'h2', 'h3', 'a', 'img'
        ]
        allowed_attrs = {
            'a': ['href', 'target'],
            'img': ['src', 'alt', 'style'],
            '*': ['style']  # осторожно: style может содержать JS!
        }
        # Удаляем потенциально опасные стили (например, expression, url(javascript:...))
        cleaned = bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attrs, strip=True)
        return cleaned


# ----------------------------
# Универсальный файл (вопрос или ответ)
# ----------------------------

def attachment_upload_path(instance, filename):
    """Динамический путь: questions/question_<id>/ или answers/question_<id>/"""
    folder = 'questions' if instance.content_type.model == 'question' else 'answers'
    return f'{folder}/question_{instance.object_id}/{filename}'


class AttachedFile(models.Model):
    # Связь с объектом (вопрос или ответ)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    file = models.FileField(
        upload_to=attachment_upload_path,
        verbose_name="Файл",
        validators=[validate_file_size, validate_file_type]
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
        verbose_name = "Прикреплённый файл"
        verbose_name_plural = "Прикреплённые файлы"
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.name or Path(self.file.name).name

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = Path(self.file.name).name
        super().save(*args, **kwargs)

    def get_file_icon(self):
        ext = Path(self.file.name).suffix.lower()
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
        try:
            size = self.file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "Неизвестно"


# ----------------------------
# Сигнал: удаление файла с диска
# ----------------------------

from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver(post_delete, sender=AttachedFile)
def delete_file_on_delete(sender, instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)