const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('.main-nav');
menuButton?.addEventListener('click', () => {
  const open = menuButton.getAttribute('aria-expanded') === 'true';
  menuButton.setAttribute('aria-expanded', String(!open));
  navigation.classList.toggle('open', !open);
});
navigation?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
  navigation.classList.remove('open');
  menuButton?.setAttribute('aria-expanded', 'false');
}));
document.querySelector('.contact-form')?.addEventListener('submit', event => {
  event.preventDefault();
  const status = event.currentTarget.querySelector('.form-status');
  status.textContent = 'Cảm ơn bạn — đây là bản demo tĩnh, biểu mẫu không gửi dữ liệu.';
});
document.querySelector('.newsletter')?.addEventListener('submit', event => {
  event.preventDefault();
  event.currentTarget.querySelector('.newsletter-status').textContent = 'Bản demo tĩnh — chưa đăng ký email.';
});
