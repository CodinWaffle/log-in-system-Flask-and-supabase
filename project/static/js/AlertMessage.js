document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert');
    if (!alerts.length) return;

    alerts.forEach(function (alertElement) {
        setTimeout(function () {
            alertElement.style.opacity = '0';
            alertElement.style.height = '0';
            alertElement.style.margin = '0';
            alertElement.style.padding = '0';
            setTimeout(function () {
                const parent = alertElement.parentElement;
                alertElement.remove();
                
                if (parent && parent.querySelectorAll && parent.querySelectorAll('.alert').length === 0) {
                    if (parent.classList && (parent.classList.contains('mt-3') || parent.classList.contains('container'))) {
                        parent.remove();
                    }
                }
            }, 600);
        }, 5000);
    });
});