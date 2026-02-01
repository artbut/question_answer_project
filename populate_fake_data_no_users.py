import os
import django
import random
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'question_answer_project.settings')
django.setup()

from qa_app.models import Category, Question
from django.contrib.auth.models import User


def fix_existing_categories():
    """Исправляем существующие категории с пустыми slug"""
    print("Проверка и исправление категорий...")

    categories = Category.objects.all()
    fixed_count = 0

    for category in categories:
        if not category.slug or category.slug.strip() == '':
            # Создаем slug из названия
            new_slug = slugify(category.name)
            if not new_slug:
                new_slug = f'category-{category.id}'

            # Проверяем уникальность
            counter = 1
            original_slug = new_slug
            while Category.objects.filter(slug=new_slug).exclude(id=category.id).exists():
                new_slug = f'{original_slug}-{counter}'
                counter += 1

            category.slug = new_slug
            category.save()
            fixed_count += 1
            print(f"  Исправлена категория '{category.name}': slug = '{category.slug}'")

    if fixed_count > 0:
        print(f"✅ Исправлено {fixed_count} категорий")
    else:
        print("✅ Категории в порядке")


def create_or_get_categories():
    """Создаем или получаем категории с корректными slug"""
    print("\nСоздание категорий...")

    categories_data = [
        {'name': 'Программирование', 'description': 'Вопросы по программированию и разработке'},
        {'name': 'Дизайн', 'description': 'Вопросы по дизайну и UX/UI'},
        {'name': 'Маркетинг', 'description': 'Вопросы по маркетингу и продвижению'},
        {'name': 'Администрирование', 'description': 'Вопросы по системному администрированию'},
        {'name': 'Базы данных', 'description': 'Вопросы по базам данных и SQL'},
        {'name': 'Мобильная разработка', 'description': 'Вопросы по разработке мобильных приложений'},
        {'name': 'Веб-разработка', 'description': 'Вопросы по веб-разработке'},
        {'name': 'DevOps', 'description': 'Вопросы по DevOps и инфраструктуре'},
        {'name': 'Тестирование', 'description': 'Вопросы по тестированию ПО'},
        {'name': 'Карьера', 'description': 'Вопросы по карьере в IT'},
    ]

    categories = []

    for cat_data in categories_data:
        # Создаем slug
        slug = slugify(cat_data['name'])
        if not slug:
            slug = f'category-{len(categories) + 1}'

        # Проверяем уникальность
        counter = 1
        original_slug = slug
        while Category.objects.filter(slug=slug).exists():
            slug = f'{original_slug}-{counter}'
            counter += 1

        # Создаем или получаем категорию
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'slug': slug,
                'description': cat_data['description']
            }
        )

        if created:
            print(f"  Создана категория: {category.name} (slug: {category.slug})")
        else:
            # Обновляем slug если он пустой или некорректный
            if not category.slug or category.slug.strip() == '':
                category.slug = slug
                category.save()
                print(f"  Обновлена категория: {category.name} (новый slug: {category.slug})")

        categories.append(category)

    print(f"✅ Готово: {len(categories)} категорий")
    return categories


def get_or_create_test_user():
    """Получаем или создаем тестового пользователя"""
    try:
        # Пробуем получить существующего пользователя
        user = User.objects.first()
        if not user:
            # Создаем тестового пользователя
            user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
            user.save()
            print(f"Создан тестовый пользователь: {user.username}")
        return user
    except Exception as e:
        print(f"Ошибка при работе с пользователем: {e}")
        return None


def create_sample_questions(categories):
    """Создаем примерные вопросы"""
    print("\nСоздание примерных вопросов...")

    sample_questions = [
        {
            'title': 'Как установить Django на Windows?',
            'content': '''
            <h3>Проблема с установкой Django</h3>
            <p>Пытаюсь установить Django на Windows 10, но возникают ошибки. Какая правильная последовательность действий?</p>

            <h4>Что я пробовал:</h4>
            <ul>
                <li>Установил Python 3.11</li>
                <li>Пробовал команду: pip install django</li>
                <li>Получаю ошибку связанную с путями</li>
            </ul>
            ''',
            'answer': '''
            <h3>Пошаговая инструкция по установке Django на Windows</h3>

            <h4>Шаг 1: Установите Python</h4>
            <p>Скачайте с <a href="https://python.org">python.org</a>, обязательно отметьте "Add Python to PATH"</p>

            <h4>Шаг 2: Проверьте установку</h4>
            <pre><code class="language-bash">
python --version
pip --version
            </code></pre>

            <h4>Шаг 3: Установите Django</h4>
            <pre><code class="language-bash">
pip install django
            </code></pre>

            <h4>Шаг 4: Проверьте установку Django</h4>
            <pre><code class="language-bash">
python -m django --version
            </code></pre>

            <h4>Шаг 5: Создайте проект</h4>
            <pre><code class="language-bash">
django-admin startproject myproject
cd myproject
python manage.py runserver
            </code></pre>

            <p><strong>Совет:</strong> Рекомендую использовать виртуальные окружения</p>
            ''',
            'tags': 'django, python, windows, установка, настройка',
            'category': 'Программирование'
        },
        {
            'title': 'Что такое миграции в Django и как с ними работать?',
            'content': '''
            <h3>Вопрос о миграциях Django</h3>
            <p>Не до конца понимаю концепцию миграций. Объясните простыми словами:</p>
            <ul>
                <li>Что такое миграции?</li>
                <li>Как они работают?</li>
                <li>Какие команды использовать?</li>
            </ul>
            ''',
            'answer': '''
            <h3>Миграции в Django - подробное объяснение</h3>

            <h4>Что такое миграции?</h4>
            <p>Миграции - это способ управления изменениями в схеме базы данных. Это файлы Python, которые описывают изменения моделей.</p>

            <h4>Основные команды:</h4>

            <div class="alert alert-info">
            <h5>1. Создание миграций</h5>
            <pre><code class="language-bash">
# После изменения models.py
python manage.py makemigrations
            </code></pre>
            <p>Создает файлы миграций в папке migrations/</p>
            </div>

            <div class="alert alert-success">
            <h5>2. Применение миграций</h5>
            <pre><code class="language-bash">
# Применяет миграции к базе данных
python manage.py migrate
            </code></pre>
            <p>Создает/изменяет таблицы в БД</p>
            </div>

            <div class="alert alert-warning">
            <h5>3. Просмотр SQL</h5>
            <pre><code class="language-bash">
# Посмотреть SQL который будет выполнен
python manage.py sqlmigrate app_name migration_number
            </code></pre>
            </div>

            <h4>Пример работы:</h4>
            <pre><code class="language-python">
# models.py - было
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

# models.py - стало (добавили поле)
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)  # ← НОВОЕ ПОЛЕ
            </code></pre>

            <pre><code class="language-bash">
# После изменения models.py
python manage.py makemigrations
python manage.py migrate
            </code></pre>

            <p><strong>Важно:</strong> Миграции должны добавляться в систему контроля версий (git)</p>
            ''',
            'tags': 'django, миграции, базы данных, модели',
            'category': 'Программирование'
        },
        {
            'title': 'Как оптимизировать запросы к базе данных в Django?',
            'content': '''
            <h3>Проблема с производительностью</h3>
            <p>Мое Django приложение стало медленно работать при большом количестве данных. В логах вижу много SQL запросов.</p>

            <pre><code class="language-python">
# Пример кода который работает медленно
def user_profile(request, user_id):
    user = User.objects.get(id=user_id)
    posts = Post.objects.filter(author=user)
    comments = Comment.objects.filter(author=user)

    for post in posts:
        post.likes_count = Like.objects.filter(post=post).count()

    return render(request, 'profile.html', {
        'user': user,
        'posts': posts,
        'comments': comments
    })
            </code></pre>
            ''',
            'answer': '''
            <h3>Оптимизация запросов в Django</h3>

            <h4>Основная проблема: N+1 Query Problem</h4>
            <p>В вашем коде выполняется один запрос для пользователя, затем N запросов для постов, и еще N запросов для лайков.</p>

            <h4>Решение 1: select_related и prefetch_related</h4>
            <pre><code class="language-python">
def optimized_profile(request, user_id):
    # select_related для ForeignKey (один-к-одному)
    user = User.objects.select_related('profile').get(id=user_id)

    # prefetch_related для обратных связей и ManyToMany
    posts = Post.objects.filter(author=user).prefetch_related(
        Prefetch('like_set', queryset=Like.objects.all(), to_attr='likes')
    )

    # Аннотации для агрегации
    from django.db.models import Count
    posts = posts.annotate(likes_count=Count('like'))

    comments = Comment.objects.filter(author=user).select_related('post')

    return render(request, 'profile.html', {
        'user': user,
        'posts': posts,
        'comments': comments
    })
            </code></pre>

            <h4>Решение 2: Использование annotate и aggregate</h4>
            <pre><code class="language-python">
from django.db.models import Count, Sum, Avg

# Вместо цикла с count()
posts = Post.objects.filter(author=user).annotate(
    likes_count=Count('like'),
    comments_count=Count('comment')
)
            </code></pre>

            <h4>Решение 3: Индексы в базе данных</h4>
            <pre><code class="language-python">
class Post(models.Model):
    title = models.CharField(max_length=200, db_index=True)  # ← Индекс
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # ← Индекс
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['author', 'created_at']),  # Составной индекс
        ]
            </code></pre>

            <h4>Решение 4: Кеширование</h4>
            <pre><code class="language-python">
from django.core.cache import cache
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Кеш на 15 минут
def user_profile(request, user_id):
    # ...
            </code></pre>

            <h4>Инструменты для диагностики:</h4>
            <ul>
                <li><strong>django-debug-toolbar</strong> - показывает все запросы</li>
                <li><strong>django-silk</strong> - профилирование</li>
                <li><strong>EXPLAIN</strong> в PostgreSQL - анализ запросов</li>
            </ul>
            ''',
            'tags': 'django, оптимизация, базы данных, производительность, запросы',
            'category': 'Базы данных'
        }
    ]

    user = get_or_create_test_user()

    for i, q_data in enumerate(sample_questions, 1):
        try:
            # Находим категорию
            category = next((c for c in categories if c.name == q_data.get('category', 'Программирование')),
                            categories[0])

            # Проверяем не существует ли уже такой вопрос
            existing = Question.objects.filter(title=q_data['title']).first()
            if existing:
                print(f"  Вопрос уже существует: '{q_data['title']}'")
                continue

            # Создаем вопрос
            question = Question.objects.create(
                title=q_data['title'],
                content=q_data['content'].strip(),
                answer=q_data.get('answer', '').strip(),
                category=category,
                author=user,
                tags=q_data['tags'],
                created_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                updated_at=timezone.now() - timedelta(days=random.randint(0, 15)),
                is_published=True,
                views=random.randint(100, 2000)
            )
            print(f"  Создан вопрос {i}: '{question.title}'")

        except Exception as e:
            print(f"  Ошибка создания вопроса '{q_data['title']}': {e}")


def create_random_questions(categories, num_questions=20):
    """Создаем случайные вопросы"""
    print(f"\nСоздание {num_questions} случайных вопросов...")

    topics = [
        ('Python', ['функции', 'классы', 'декораторы', 'генераторы', 'асинхронность']),
        ('Django', ['модели', 'вьюхи', 'формы', 'шаблоны', 'REST API']),
        ('JavaScript', ['React', 'Vue', 'Node.js', 'TypeScript', 'Webpack']),
        ('Базы данных', ['PostgreSQL', 'MySQL', 'Redis', 'индексы', 'транзакции']),
        ('DevOps', ['Docker', 'Kubernetes', 'CI/CD', 'мониторинг', 'логирование'])
    ]

    user = get_or_create_test_user()
    questions_created = 0

    for i in range(num_questions):
        try:
            # Выбираем случайную тему
            topic, subtopics = random.choice(topics)
            subtopic = random.choice(subtopics)

            # Генерируем заголовок
            question_words = ['Как', 'Почему', 'Каким образом', 'Что делать если', 'В чем разница между']
            title = f"{random.choice(question_words)} {subtopic} в {topic}?"

            # Проверяем не существует ли уже
            if Question.objects.filter(title=title).exists():
                title = f"{title} (вариант {i + 1})"

            # Простой контент
            content = f"<p>У меня вопрос по {subtopic} в {topic}. Можете объяснить подробно?</p>"

            # 60% шанс что будет ответ
            has_answer = random.random() < 0.6
            answer = f"<p>Ответ на вопрос по {subtopic} в {topic}.</p>" if has_answer else ''

            # Создаем вопрос
            question = Question.objects.create(
                title=title,
                content=content,
                answer=answer,
                category=random.choice(categories),
                author=user,
                tags=f"{topic.lower()}, {subtopic}",
                created_at=timezone.now() - timedelta(days=random.randint(1, 90)),
                updated_at=timezone.now() - timedelta(
                    days=random.randint(0, 30)) if has_answer else timezone.now() - timedelta(
                    days=random.randint(1, 90)),
                is_published=True,
                views=random.randint(50, 1500)
            )

            questions_created += 1
            if questions_created % 5 == 0:
                print(f"  Создано {questions_created}/{num_questions} вопросов")

        except Exception as e:
            print(f"  Ошибка создания случайного вопроса: {e}")
            continue

    print(f"✅ Создано {questions_created} случайных вопросов")


def main():
    """Основная функция"""
    print("=" * 60)
    print("ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ ДЛЯ Q&A")
    print("=" * 60)

    # 1. Исправляем существующие категории
    fix_existing_categories()

    # 2. Создаем или получаем категории
    categories = create_or_get_categories()

    # 3. Создаем примерные вопросы
    create_sample_questions(categories)

    # 4. Создаем случайные вопросы
    create_random_questions(categories, num_questions=15)

    # 5. Выводим статистику
    print("\n" + "=" * 60)
    print("ФИНАЛЬНАЯ СТАТИСТИКА:")
    print(f"Категории: {Category.objects.count()}")
    print(f"Всего вопросов: {Question.objects.count()}")
    print(f"Вопросов с ответами: {Question.objects.exclude(answer='').count()}")
    print(f"Вопросов без ответов: {Question.objects.filter(answer='').count()}")

    # Показываем несколько примеров
    print("\nПОСЛЕДНИЕ СОЗДАННЫЕ ВОПРОСЫ:")
    for q in Question.objects.order_by('-created_at')[:3]:
        answer_status = '✓' if q.answer else '✗'
        print(f"  {answer_status} {q.title[:50]}...")

    print("\n✅ Тестовые данные успешно созданы!")
    print("Сайт готов к тестированию.")


if __name__ == '__main__':
    main()