(function () {
  const modal = document.getElementById('loginModal');

  window.openLoginModal = function openLoginModal() {
    if (!modal) return;
    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
  };

  window.closeLoginModal = function closeLoginModal() {
    if (!modal) return;
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
  };

  window.switchToRegisterModal = function switchToRegisterModal() {
    // Hàm openRegisterModal() có thể được định nghĩa ở template khác
    if (typeof window.openRegisterModal === 'function') {
      closeLoginModal();
      window.openRegisterModal();
    }
  };

  // Đóng khi click ra ngoài
  window.addEventListener('click', function (e) {
    if (!modal) return;
    if (e.target === modal) closeLoginModal();
  });

  // Đóng bằng phím ESC
  window.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeLoginModal();
  });
})();
