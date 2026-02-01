from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.urls import reverse
from django.utils.html import format_html

from .models import Category, Question, Tag, AttachedFile, Task, TaskNote, SearchQuery


# ----------------------------
# Вложенные файлы через GenericForeignKey
# ----------------------------

class AttachedFileInline(GenericTabularInline):
    """
    Инлайн для прикреплённых файлов.
    Работает с любыми моделями: Question, Task, TaskNote и др.
    """
    model = AttachedFile
    extra = 0
    readonly_fields = ('uploaded_at', 'get_file_size', 'download_link')
    fields = ('file', 'name', 'uploaded_by', 'uploaded_at', 'get_file_size', 'download_link')

    def get_file_size(self, obj):
        return obj.get_file_size()
    get_file_size.short_description = "Размер"

    def download_link(self, obj):
        if obj.file:
            url = obj.file.url
            return format_html('<a href="{}" target="_blank">⬇️ Скачать</a>', url)
        return "-"
    download_link.short_description = "Скачать"
    download_link.allow_tags = True


# ----------------------------
# Записи по задаче (вложенные в Task)
# ----------------------------

class TaskNoteInline(admin.StackedInline):
    """
    Записи, связанные с задачей — инструкции, шаги, комментарии.
    """
    model = TaskNote
    extra = 1
    fields = ('title', 'content', 'order', 'author')
    readonly_fields = ('author',)
    ordering = ('order',)

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


# ----------------------------
# Админка: Категория
# ----------------------------

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'question_count', 'description_preview')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    list_per_page = 20

    def question_count(self, obj):
        return obj.question_set.filter(is_published=True).count()
    question_count.short_description = "Вопросов"

    def description_preview(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_preview.short_description = "Описание"


# ----------------------------
# Админка: Тег
# ----------------------------

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'usage_count')
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 20

    def usage_count(self, obj):
        # Подсчёт использования тега в вопросах
        return obj.question_set.count()
    usage_count.short_description = "Использовано"


# ----------------------------
# Админка: Вопрос
# ----------------------------

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'author', 'created_at',
        'is_published', 'has_answer', 'views'
    )
    list_filter = (
        'is_published', 'category', 'created_at', 'tags',
        'author'
    )
    search_fields = ('title', 'content', 'answer', 'tags__name', 'author__username')
    list_editable = ('is_published',)
    readonly_fields = ('created_at', 'updated_at', 'views')
    filter_horizontal = ('tags',)
    inlines = [AttachedFileInline]
    ordering = ('-created_at',)
    list_per_page = 15
    date_hierarchy = 'created_at'
    save_as = True

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'content', 'category', 'tags')
        }),
        ('Ответ', {
            'fields': ('answer',),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('author', 'is_published', 'views', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_answer(self, obj):
        return bool(obj.answer and obj.answer.strip())
    has_answer.boolean = True
    has_answer.short_description = "Есть ответ"


# ----------------------------
# Админка: Задача (Task)
# ----------------------------

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'created_at', 'question_link',
        'notes_count', 'files_count'
    )
    list_filter = ('created_at', 'author', 'question')
    search_fields = ('title', 'description', 'author__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TaskNoteInline, AttachedFileInline]
    ordering = ('-created_at',)
    list_per_page = 15
    save_as = True

    fieldsets = (
        ('Задача', {
            'fields': ('title', 'description', 'author')
        }),
        ('Связь', {
            'fields': ('question',),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def question_link(self, obj):
        if obj.question:
            url = reverse('admin:qa_app_question_change', args=[obj.question.pk])
            return format_html('<a href="{}">{}</a>', url, obj.question.title)
        return "-"
    question_link.short_description = "Связанный вопрос"
    question_link.allow_tags = True

    def notes_count(self, obj):
        return obj.notes.count()
    notes_count.short_description = "Записей"

    def files_count(self, obj):
        content_type = obj.get_content_type()
        return AttachedFile.objects.filter(content_type=content_type, object_id=obj.pk).count()
    files_count.short_description = "Файлов"


# ----------------------------
# Админка: Запись по задаче (TaskNote)
# ----------------------------

@admin.register(TaskNote)
class TaskNoteAdmin(admin.ModelAdmin):
    list_display = ('task', 'title_preview', 'author', 'created_at', 'order')
    list_filter = ('task', 'author', 'created_at')
    search_fields = ('content', 'title', 'task__title')
    readonly_fields = ('created_at', 'updated_at', 'author')
    ordering = ('task', 'order', 'created_at')
    list_per_page = 20

    fieldsets = (
        ('Запись', {
            'fields': ('task', 'title', 'content', 'order')
        }),
        ('Автор и время', {
            'fields': ('author', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def title_preview(self, obj):
        return obj.title or f"Запись #{obj.id}"
    title_preview.short_description = "Заголовок"

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


# ----------------------------
# Админка: Прикреплённые файлы (отдельно)
# ----------------------------

@admin.register(AttachedFile)
class AttachedFileAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'linked_object', 'content_type',
        'uploaded_by', 'uploaded_at', 'get_file_size'
    )
    list_filter = ('content_type', 'uploaded_at', 'uploaded_by')
    search_fields = ('name', 'object_id')
    readonly_fields = ('uploaded_at', 'get_file_size', 'download_link')
    raw_id_fields = ('uploaded_by',)
    list_per_page = 20

    def linked_object(self, obj):
        if obj.content_object:
            try:
                url = reverse(
                    f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                    args=[obj.object_id]
                )
                return format_html('<a href="{}">{}</a>', url, obj.content_object)
            except Exception:
                return str(obj.content_object)
        return "-"
    linked_object.allow_tags = True
    linked_object.short_description = "Связанный объект"

    def get_file_size(self, obj):
        return obj.get_file_size()
    get_file_size.short_description = "Размер"

    def download_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">⬇️ Скачать</a>', obj.file.url)
        return "-"
    download_link.short_description = "Скачать"
    download_link.allow_tags = True


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ['term', 'user', 'ip_address', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['term', 'ip_address']
    readonly_fields = ['created_at']