from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from pathlib import Path
import os


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
# Универсальный файл (вопрос, ответ, задача, запись)
# ----------------------------

def attachment_upload_path(instance, filename):
    """Динамический путь: tasks/task_<id>/ или questions/question_<id>/"""
    model = instance.content_type.model
    obj_id = instance.object_id
    if model == 'task':
        folder = 'tasks'
    elif model == 'tasknote':
        folder = 'task_notes'
    elif model == 'question':
        folder = 'questions'
    else:
        folder = 'files'
    return f'{folder}/{model}_{obj_id}/{filename}'


class AttachedFile(models.Model):
    # Связь с объектом (задача, запись, вопрос и т.д.)
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
# Вопрос
# ----------------------------

class Question(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок вопроса")
    content = models.TextField(verbose_name="Содержание вопроса")  # Заменено на TextField для простоты
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
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Теги")
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    attachedfile_set = GenericRelation(AttachedFile)

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


# ----------------------------
# Task — задача без статуса, просто контейнер для записей и файлов
# ----------------------------

class Task(models.Model):
    """
    Задача как тема для хранения инструкций, порядка выполнения, сроков и вложений.
    Не имеет статуса — только заголовок, описание и связь с автором.
    """
    title = models.CharField(max_length=200, verbose_name="Название задачи")
    description = models.TextField(blank=True, verbose_name="Описание / цель")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")

    # Опционально: привязка к вопросу
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Связанный вопрос")

    # Прямая ссылка на прикреплённые файлы (через GenericRelation)
    attachedfile_set = GenericRelation(AttachedFile)

    class Meta:
        verbose_name = "Задача (запись)"
        verbose_name_plural = "Задачи (записи)"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('qa_app:task_detail', kwargs={'pk': self.pk})


# ----------------------------
# TaskNote — запись по задаче (инструкция, шаги, заметки)
# ----------------------------

class TaskNote(models.Model):
    """
    Детальная запись по задаче: порядок выполнения, сроки, комментарии, напоминания.
    Может содержать форматированный текст.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notes', verbose_name="Задача")
    title = models.CharField(max_length=200, verbose_name="Заголовок записи", blank=True)
    content = models.TextField(verbose_name="Содержание")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок", help_text="Для сортировки записей")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")

    class Meta:
        verbose_name = "Запись по задаче"
        verbose_name_plural = "Записи по задаче"
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.title or 'Запись'} — {self.task.title}"

    # Прямая ссылка на прикреплённые файлы
    attachedfile_set = GenericRelation(AttachedFile)


# ----------------------------
# Сигнал: удаление файла с диска
# ----------------------------

@receiver(post_delete, sender=AttachedFile)
def delete_file_on_delete(sender, instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        try:
            os.remove(instance.file.path)
        except OSError:
            pass  # Файл уже удалён или недоступен


class SearchQuery(models.Model):
    """
    Модель для хранения поисковых запросов и анализа популярных тем.
    Используется для отображения "Популярные запросы" на странице поиска.
    """
    term = models.CharField(max_length=255, verbose_name="Поисковый запрос")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь"
    )
    ip_address = models.GenericIPAddressField(
        verbose_name="IP-адрес",
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        verbose_name="User Agent",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        default=datetime.now,
        verbose_name="Дата и время"
    )

    class Meta:
        verbose_name = "Поисковый запрос"
        verbose_name_plural = "Поисковые запросы"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['term']),
            models.Index(fields=['user']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f"{self.term} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"