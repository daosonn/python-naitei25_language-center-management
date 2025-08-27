// Fetch unread notifications and update bell badge
function updateNotificationBell() {
  fetch('/notifications/api/unread/')
    .then(res => res.json())
    .then(data => {
      const badge = document.getElementById('notificationBadge');
      if (badge) {
        if (data.count > 0) {
          badge.textContent = data.count;
          badge.style.display = '';
        } else {
          badge.style.display = 'none';
        }
      }
      // Optionally, render notification list in a dropdown/modal
      // ...
    });
}

document.addEventListener('DOMContentLoaded', function() {
  updateNotificationBell();
  // Optionally, poll every 30s
  setInterval(updateNotificationBell, 30000);

  // Show notifications on bell click (simple dropdown)
  const bell = document.getElementById('notificationBell');
  if (bell) {
    bell.addEventListener('click', function(e) {
      e.preventDefault();
      fetch('/notifications/api/unread/')
        .then(res => res.json())
        .then(data => {
          let html = '';
          if (data.notifications.length === 0) {
            html = '<div class="p-2 text-muted">Không có thông báo mới.</div>';
          } else {
            html = data.notifications.map(n => `<div class="p-2 border-bottom small">${n.message}<br><span class='text-muted'>${n.created_at}</span></div>`).join('');
          }
          let dropdown = document.getElementById('notificationDropdown');
          if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.id = 'notificationDropdown';
            dropdown.style.position = 'absolute';
            dropdown.style.top = '40px';
            dropdown.style.right = '0';
            dropdown.style.minWidth = '250px';
            dropdown.style.background = '#fff';
            dropdown.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
            dropdown.style.zIndex = '9999';
            dropdown.className = 'border rounded';
            bell.parentNode.appendChild(dropdown);
          }
          dropdown.innerHTML = html;
          dropdown.style.display = 'block';
          // Hide on click outside
          document.addEventListener('click', function handler(ev) {
            if (!dropdown.contains(ev.target) && ev.target !== bell) {
              dropdown.style.display = 'none';
              document.removeEventListener('click', handler);
            }
          });
        });
    });
  }
});
