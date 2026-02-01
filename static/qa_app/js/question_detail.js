document.addEventListener('DOMContentLoaded', function() {
    const question = document.getElementById('question');
    const addAnswerBtn = document.getElementById('addAnswerBtn');
    const editAnswerBtn = document.getElementById('editAnswerBtn');
    const answerContent = document.getElementById('answerContent');
    const answerAuthor = document.getElementById('answerAuthor');
    const answerDate = document.getElementById('answerDate');
    const filesContainer = document.getElementById('filesContainer');
    const deleteAnswerBtn = document.getElementById('deleteAnswerBtn');

    // Обновление ответа после успешного AJAX-запроса
    function updateAnswerUI(data) {
        if (data.has_answer) {
            // Показываем ответ
            answerContent.innerHTML = data.answer;
            answerAuthor.textContent = data.answer_author.username;
            answerDate.textContent = data.updated_at;

            // Обновляем файлы, если есть
            if (data.files && data.total_files > 0) {
                updateFilesList(data.files);
            }

            // Переключаем кнопки
            if (addAnswerBtn) addAnswerBtn.classList.add('d-none');
            if (editAnswerBtn) editAnswerBtn.classList.remove('d-none');
            if (deleteAnswerBtn) deleteAnswerBtn.classList.remove('d-none');

            // Уведомление
            showNotification(data.message, 'success');
        } else {
            // Ответ удалён
            answerContent.innerHTML = '<em>Ответ отсутствует</em>';
            answerAuthor.textContent = '';
            answerDate.textContent = '';

            // Очищаем файлы
            if (filesContainer) {
                filesContainer.innerHTML = '<p class="text-muted">Нет прикреплённых файлов</p>';
            }

            // Переключаем кнопки
            if (addAnswerBtn) addAnswerBtn.classList.remove('d-none');
            if (editAnswerBtn) editAnswerBtn.classList.add('d-none');
            if (deleteAnswerBtn) deleteAnswerBtn.classList.add('d-none');

            showNotification(data.message, 'info');
        }
    }

    // Обновление списка файлов
    function updateFilesList(files) {
        if (!filesContainer) return;

        filesContainer.innerHTML = '';
        if (files.length === 0) {
            filesContainer.innerHTML = '<p class="text-muted">Нет прикреплённых файлов</p>';
            return;
        }

        files.forEach(file => {
            const fileEl = document.createElement('div');
            fileEl.className = 'alert alert-light d-flex align-items-center mb-2';
            fileEl.innerHTML = `
                <i class="${file.icon} me-3 text-secondary"></i>
                <div class="flex-grow-1">
                    <div><strong>${escapeHtml(file.name)}</strong></div>
                    <small class="text-muted">${file.size}</small>
                </div>
                <a href="${file.url}" class="btn btn-sm btn-outline-primary" download>
                    <i class="fas fa-download"></i>
                </a>
                <button type="button" class="btn btn-sm btn-outline-danger ms-1" 
                        onclick="deleteFile(${file.id})">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            filesContainer.appendChild(fileEl);
        });
    }

    // Экранирование HTML для безопасности
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Показ уведомления
    function showNotification(message, type = 'info') {
        let bgColor;
        switch (type) {
            case 'success': bgColor = '#d1e7dd'; break;
            case 'error': bgColor = '#f8d7da'; break;
            default: bgColor = '#fff3cd';
        }

        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${bgColor};
            border: 1px solid #ccc;
            padding: 12px 16px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            font-size: 14px;
            max-width: 300px;
            transition: opacity 0.3s;
        `;
        notification.innerHTML = `
            <strong>${message}</strong>
        `;

        document.body.appendChild(notification);
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
    }

    // Глобальная функция удаления файла
    window.deleteFile = function(fileId) {
        if (!confirm('Удалить этот файл?')) return;

        fetch(`/qa/delete-file/${fileId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Файл удалён', 'success');
                // Перезагружаем страницу, чтобы обновить состояние
                location.reload();
            } else {
                showNotification('Ошибка: ' + (data.error || 'Неизвестная ошибка'), 'error');
            }
        })
        .catch(() => {
            showNotification('Ошибка сети', 'error');
        });
    };

    // Получение CSRF-токена
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Инициализация CKEditor (если используется)
    if (typeof ClassicEditor !== 'undefined') {
        const editors = ['answerContent', 'editAnswerContent'];
        editors.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                ClassicEditor.create(el, {
                    toolbar: ['bold', 'italic', 'link', 'bulletedList', 'numberedList', 'blockQuote'],
                    language: 'ru'
                }).catch(error => console.error(`Ошибка инициализации редактора ${id}:`, error));
            }
        });
    }
});