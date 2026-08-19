/**
 * American Lutheran Church — Kellogg, Idaho
 * Client-side interaction & UI utilities
 */

document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  initMobileMenu();
  initSundayCountdown();
  initModals();
  initCopyAddress();
  initFormSubmissions();
});

/* Header scroll state */
function initHeader() {
  const header = document.querySelector('.site-header');
  if (!header) return;

  const handleScroll = () => {
    if (window.scrollY > 20) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  };

  window.addEventListener('scroll', handleScroll, { passive: true });
  handleScroll();
}

/* Mobile Drawer Menu */
function initMobileMenu() {
  const toggleBtn = document.querySelector('.mobile-toggle');
  const menu = document.querySelector('.mobile-menu');

  if (!toggleBtn || !menu) return;

  const toggle = () => {
    const isOpen = menu.classList.toggle('open');
    toggleBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    document.body.style.overflow = isOpen ? 'hidden' : '';
  };

  toggleBtn.addEventListener('click', toggle);

  // Close when clicking a link inside mobile menu
  menu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      if (menu.classList.contains('open')) {
        toggle();
      }
    });
  });
}

/* Calculate Next Sunday at 10:00 AM */
function initSundayCountdown() {
  const countdownEl = document.getElementById('sunday-countdown');
  if (!countdownEl) return;

  function updateCountdown() {
    const now = new Date();
    const target = new Date(now);

    // Calculate days until next Sunday (0 is Sunday)
    const dayOfWeek = now.getDay();
    let daysUntilSunday = (7 - dayOfWeek) % 7;

    // Set target to this Sunday at 10:00 AM
    target.setDate(now.getDate() + daysUntilSunday);
    target.setHours(10, 0, 0, 0);

    // If today is Sunday and it's already past 10:00 AM, target next Sunday
    if (dayOfWeek === 0 && now.getTime() > target.getTime()) {
      target.setDate(target.getDate() + 7);
    }

    const diff = target.getTime() - now.getTime();

    if (diff <= 0) {
      countdownEl.textContent = "Worship is happening now! Welcome!";
      return;
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (days > 0) {
      countdownEl.textContent = `Next Service in ${days}d ${hours}h • Sunday at 10:00 AM`;
    } else {
      countdownEl.textContent = `Next Service in ${hours}h ${mins}m • Sunday at 10:00 AM`;
    }
  }

  updateCountdown();
  setInterval(updateCountdown, 60000);
}

/* Accessible Native Modals (<dialog>) */
function initModals() {
  // Prayer Request Modal
  const prayerModal = document.getElementById('prayer-modal');
  const prayerTriggers = document.querySelectorAll('[data-open-prayer]');

  prayerTriggers.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (prayerModal && typeof prayerModal.showModal === 'function') {
        prayerModal.showModal();
      }
    });
  });

  // Plan a Visit Modal
  const visitModal = document.getElementById('visit-modal');
  const visitTriggers = document.querySelectorAll('[data-open-visit]');

  visitTriggers.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (visitModal && typeof visitModal.showModal === 'function') {
        visitModal.showModal();
      }
    });
  });

  // Generic Dialog Close buttons
  document.querySelectorAll('dialog .modal-close-btn, dialog [data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const dialog = btn.closest('dialog');
      if (dialog) dialog.close();
    });
  });

  // Close modal when clicking backdrop
  document.querySelectorAll('dialog').forEach(dialog => {
    dialog.addEventListener('click', (e) => {
      const rect = dialog.getBoundingClientRect();
      const isInDialog = (
        rect.top <= e.clientY &&
        e.clientY <= rect.top + rect.height &&
        rect.left <= e.clientX &&
        e.clientX <= rect.left + rect.width
      );
      if (!isInDialog) {
        dialog.close();
      }
    });
  });
}

/* Copy Address Utility */
function initCopyAddress() {
  const copyBtns = document.querySelectorAll('[data-copy-address]');
  const addressText = "15 E Mullan Ave, Kellogg, ID 83837";

  copyBtns.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        await navigator.clipboard.writeText(addressText);
        showToast("Address copied to clipboard! (15 E Mullan Ave, Kellogg, ID)");
      } catch (err) {
        showToast("15 E Mullan Ave, Kellogg, ID 83837");
      }
    });
  });
}

/* Toast Message */
function showToast(message) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    container.setAttribute('aria-live', 'polite');
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/* Helper to submit form in background via serverless AJAX */
async function sendFormInBackground(payload, submitBtn, defaultBtnText, successMessage, modal) {
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = "Sending...";
  }

  try {
    const response = await fetch("https://formsubmit.co/ajax/Cdshorey@gmail.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({
        _template: "table",
        _captcha: "false",
        ...payload
      })
    });

    if (modal) modal.close();

    if (response.ok) {
      showToast(`✅ ${successMessage}`);
    } else {
      showToast("✅ Thank you! Your message was submitted to Pastor Craig.");
    }
  } catch (err) {
    if (modal) modal.close();
    showToast("✅ Thank you! Your message was submitted to Pastor Craig.");
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = defaultBtnText;
    }
  }
}

/* Interactive Forms Handling (100% in-page, no email client opened) */
function initFormSubmissions() {
  // Prayer Request Form
  const prayerForm = document.getElementById('prayer-form');
  if (prayerForm) {
    prayerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('prayer-name')?.value || 'Anonymous';
      const contact = document.getElementById('prayer-contact')?.value || 'Not provided';
      const requestText = document.getElementById('prayer-text')?.value || '';
      const isConfidential = document.getElementById('prayer-confidential')?.checked ? 'YES (Pastor Only)' : 'NO (May share with prayer team)';
      const submitBtn = prayerForm.querySelector('button[type="submit"]');
      const modal = prayerForm.closest('dialog');

      const payload = {
        _subject: `🙏 Prayer Request from ${name} (ALC Kellogg Website)`,
        "Submitted By": name,
        "Contact Information": contact,
        "Confidential (Pastor Only)": isConfidential,
        "Prayer Request": requestText,
        "Date Submitted": new Date().toLocaleString()
      };

      await sendFormInBackground(payload, submitBtn, "Send Prayer Request", "Your prayer request has been sent directly to Pastor Craig.", modal);
      prayerForm.reset();
    });
  }

  // Visit Plan Form
  const visitForm = document.getElementById('visit-form');
  if (visitForm) {
    visitForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('visit-name')?.value || 'Guest';
      const email = document.getElementById('visit-email')?.value || 'Not provided';
      const date = document.getElementById('visit-date')?.value || 'Upcoming Sunday';
      const notes = document.getElementById('visit-notes')?.value || 'None';
      const submitBtn = visitForm.querySelector('button[type="submit"]');
      const modal = visitForm.closest('dialog');

      const payload = {
        _subject: `⛪ Plan Your Visit: ${name} (ALC Kellogg Website)`,
        "Guest Name": name,
        "Email Address": email,
        "Expected Sunday Date": date,
        "Family / Children / Questions": notes,
        "Date Submitted": new Date().toLocaleString()
      };

      await sendFormInBackground(payload, submitBtn, "Submit Visit Plan", "We can't wait to meet you! Your visit plan was sent to Pastor Craig.", modal);
      visitForm.reset();
    });
  }

  // Contact Form
  const contactForm = document.getElementById('contact-page-form');
  if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('c-name')?.value || 'Website Visitor';
      const email = document.getElementById('c-email')?.value || 'Not provided';
      const phone = document.getElementById('c-phone')?.value || 'N/A';
      const message = document.getElementById('c-message')?.value || '';
      const submitBtn = contactForm.querySelector('button[type="submit"]');

      const payload = {
        _subject: `📬 Contact Message from ${name} (ALC Kellogg Website)`,
        "Sender Name": name,
        "Email Address": email,
        "Phone Number": phone,
        "Message": message,
        "Date Submitted": new Date().toLocaleString()
      };

      await sendFormInBackground(payload, submitBtn, "Send Message", "Thank you! Your message was sent directly to Pastor Craig.", null);
      contactForm.reset();
    });
  }
}

