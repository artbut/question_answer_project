// Основной JavaScript файл
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всех всплывающих подсказок
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Функция для показа уведомлений
    window.showNotification = function(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 1055;
            min-width: 300px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;

        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    };

    // Функция для форматирования размера файла
    window.formatFileSize = function(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    // Обработчик для подтверждения удаления
    document.querySelectorAll('.delete-file-form, form[onsubmit*="confirm"]').forEach(form => {
        form.onsubmit = function(e) {
            if (!confirm('Вы уверены, что хотите удалить этот файл?')) {
                e.preventDefault();
                return false;
            }
            return true;
        };
    });
});