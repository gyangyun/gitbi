// 自动隐藏消息的函数
function autoHideMessage(messageEl) {
    if (!messageEl) return;

    setTimeout(() => {
        messageEl.classList.add('fade-out');
    }, 2000);

    setTimeout(() => {
        messageEl.innerHTML = '';
        messageEl.classList.remove('fade-out');
    }, 2500);
}

// 监听消息元素的变化
document.addEventListener('DOMContentLoaded', function () {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.target.id === 'save-message' && mutation.target.innerHTML) {
                autoHideMessage(mutation.target);
            }
        });
    });

    const saveMessage = document.getElementById('save-message');
    if (saveMessage) {
        observer.observe(saveMessage, {
            childList: true,
            characterData: true,
            subtree: true
        });
    }
}); 