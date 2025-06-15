window.sonner = window.sonner || {};
window.sonner.toast = window.sonner.toast || function(type, message) {
    window.sonner[type](message, {
        style: {
            background: type === 'success' ? '#16a34a' : '#dc2626',
            color: 'white',
            border: 'none'
        }
    });
};