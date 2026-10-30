/**
 * Trackera - Vanilla JavaScript Enhancements
 * Pure Vanilla JS: No external libraries, no frameworks.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Auto-dismiss alerts after 5 seconds with fade
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach((alert) => {
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-4px)';
        setTimeout(() => alert.remove(), 250);
      });
    }

    setTimeout(() => {
      if (document.body.contains(alert)) {
        alert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-4px)';
        setTimeout(() => alert.remove(), 300);
      }
    }, 5000);
  });

  // 2. Auto-submit filter dropdowns on change
  const autoFilterSelects = document.querySelectorAll('.auto-submit-filter');
  autoFilterSelects.forEach((select) => {
    select.addEventListener('change', () => {
      const form = select.closest('form');
      if (form) {
        form.submit();
      }
    });
  });

  // 3. Quick status dropdown auto-submit
  const quickStatusForms = document.querySelectorAll('.quick-status-form select');
  quickStatusForms.forEach((select) => {
    select.addEventListener('change', (e) => {
      const form = e.target.closest('form');
      if (form) {
        form.submit();
      }
    });
  });

  // 4. Client-side number validation feedback
  const numberInputs = document.querySelectorAll('input[type="number"]');
  numberInputs.forEach((input) => {
    input.addEventListener('blur', () => {
      const val = parseFloat(input.value);
      if (isNaN(val) && input.value !== '') {
        input.style.borderColor = '#ef4444';
      } else {
        input.style.borderColor = '';
      }
    });
  });
});
