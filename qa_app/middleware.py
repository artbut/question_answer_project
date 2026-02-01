from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin


class LoginRequiredMiddleware(MiddlewareMixin):
    """Проверяет, авторизован ли пользователь для определенных страниц"""

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Страницы, требующие авторизации
        login_required_urls = [
            '/questions/create/',
            '/questions/<int:pk>/add-answer-ajax/',
            '/files/delete/',
        ]

        # Проверяем, нужно ли требовать авторизацию для этого URL
        if any(request.path.startswith(
                url.replace('<int:pk>', '').replace('<str:file_type>', '').replace('<int:file_id>', ''))
               for url in login_required_urls):
            if not request.user.is_authenticated:
                from django.shortcuts import redirect
                from django.urls import reverse
                messages.error(request, 'Для доступа к этой странице необходимо войти в систему.')
                return redirect(f'{reverse("qa_app:login")}?next={request.path}')

        return None