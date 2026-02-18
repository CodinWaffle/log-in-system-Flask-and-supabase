document.addEventListener('DOMContentLoaded', function() {
    const alertElement = document.querySelector('.alert');
    if (alertElement) {
        setTimeout(function() {
            alertElement.style.opacity = "0";
            setTimeout(function() {
                alertElement.style.display = "none";
            }, 500);
        }, 5000);
    }
});