/**
 * Hotel Bhagshree — Main JavaScript
 * Navigation, Cart, Flash Messages, Micro-animations
 */

'use strict';

// ── Utility ───────────────────────────────────────────────────────────────────
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

async function apiFetch(url, opts = {}) {
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...opts.headers },
      ...opts,
    });
    return await res.json();
  } catch (e) {
    console.error('API error:', e);
    return { success: false, message: 'Network error' };
  }
}

// ── Navigation ────────────────────────────────────────────────────────────────
function initNav() {
  const nav    = $('.nav');
  const toggle = $('.nav__toggle');
  const links  = $('.nav__links');

  if (!nav) return;

  // Scroll behaviour
  const onScroll = () => {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Mobile menu toggle
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      const open = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open);
      document.body.style.overflow = open ? 'hidden' : '';
    });

    // Close on link click
    $$('a', links).forEach(a => {
      a.addEventListener('click', () => {
        links.classList.remove('open');
        document.body.style.overflow = '';
      });
    });
  }

  // Active link highlight
  const path = window.location.pathname;
  $$('.nav__link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && path.startsWith(href)) {
      link.classList.add('active');
    } else if (href === '/' && path === '/') {
      link.classList.add('active');
    }
  });
}

// ── Cart ──────────────────────────────────────────────────────────────────────
function initCart() {
  updateCartCount();

  // Add to cart buttons
  $$('[data-add-to-cart]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const itemId = btn.dataset.addToCart;
      const qty    = parseInt(btn.dataset.qty || '1');
      
      btn.disabled = true;
      const original = btn.innerHTML;
      btn.innerHTML = '<span class="spinner"></span>';

      const data = await apiFetch('/orders/cart/add', {
        method: 'POST',
        body: JSON.stringify({ item_id: itemId, qty }),
      });

      btn.disabled = false;
      btn.innerHTML = original;

      if (data.success) {
        showToast(data.message || 'Added to cart', 'success');
        updateCartCount(data.cart_count);
        // Animate button
        btn.style.transform = 'scale(.94)';
        setTimeout(() => { btn.style.transform = ''; }, 150);
      } else {
        showToast(data.message || 'Error adding item', 'error');
      }
    });
  });
}

async function updateCartCount(count = null) {
  const badge = $('.nav__cart-count');
  if (!badge) return;

  if (count === null) {
    const data = await apiFetch('/orders/cart/count');
    count = data.count || 0;
  }

  badge.textContent = count;
  badge.style.display = count > 0 ? 'flex' : 'none';
}

// ── Cart Page ─────────────────────────────────────────────────────────────────
function initCartPage() {
  $$('[data-qty-btn]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const itemId = btn.dataset.itemId;
      const delta  = parseInt(btn.dataset.delta);
      const display = $(`[data-qty-display="${itemId}"]`);

      let current = parseInt(display?.textContent || '1');
      let newQty  = Math.max(0, current + delta);

      const data = await apiFetch('/orders/cart/update', {
        method: 'POST',
        body: JSON.stringify({ item_id: itemId, qty: newQty }),
      });

      if (data.success) {
        updateCartCount(data.cart_count);
        // Reload cart UI
        location.reload();
      }
    });
  });

  $$('[data-remove-item]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const itemId = btn.dataset.removeItem;
      const data = await apiFetch('/orders/cart/remove', {
        method: 'POST',
        body: JSON.stringify({ item_id: itemId }),
      });
      if (data.success) {
        updateCartCount(data.cart_count);
        location.reload();
      }
    });
  });
}

// ── Flash Toast Messages ──────────────────────────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
  let container = $('.flash-messages');
  if (!container) {
    container = document.createElement('div');
    container.className = 'flash-messages';
    document.body.appendChild(container);
  }

  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const toast = document.createElement('div');
  toast.className = `flash flash--${type}`;
  toast.innerHTML = `
    <span>${icons[type] || ''} ${message}</span>
    <button class="flash__close" aria-label="Close">✕</button>
  `;

  $('button', toast).addEventListener('click', () => removeToast(toast));
  container.appendChild(toast);

  if (duration > 0) {
    setTimeout(() => removeToast(toast), duration);
  }
}

function removeToast(el) {
  el.style.opacity = '0';
  el.style.transform = 'translateX(20px)';
  el.style.transition = 'all .25s ease';
  setTimeout(() => el.remove(), 250);
}

function initFlashMessages() {
  // Auto-dismiss server-rendered flash messages
  $$('.flash').forEach(flash => {
    const closeBtn = $('.flash__close', flash);
    closeBtn?.addEventListener('click', () => removeToast(flash));
    setTimeout(() => removeToast(flash), 5000);
  });
}

// ── Menu Filter Tabs ──────────────────────────────────────────────────────────
function initMenuFilters() {
  const catTabs = $$('.cat-tab');
  if (!catTabs.length) return;

  catTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      catTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const category = tab.dataset.category || '';
      filterMenuItems(category);
    });
  });

  // Filter pills (veg/non-veg, spice)
  $$('.filter-pill button[data-filter]').forEach(btn => {
    btn.addEventListener('click', () => {
      const group = btn.dataset.filterGroup;
      $$(`[data-filter-group="${group}"]`).forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      applyAllFilters();
    });
  });

  // Search
  const searchInput = $('[data-menu-search]');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(applyAllFilters, 300);
    });
  }
}

function getActiveFilter(group) {
  const btn = $(`.filter-pill button.active[data-filter-group="${group}"]`);
  return btn ? btn.dataset.filter : '';
}

function applyAllFilters() {
  const category   = ($('.cat-tab.active')?.dataset.category) || '';
  const foodType   = getActiveFilter('food_type');
  const spiceLevel = getActiveFilter('spice_level');
  const search     = ($('[data-menu-search]')?.value || '').toLowerCase().trim();

  $$('.food-card[data-item-id]').forEach(card => {
    const cardCat   = (card.dataset.category || '').toLowerCase();
    const cardType  = card.dataset.foodType || '';
    const cardSpice = card.dataset.spiceLevel || '';
    const cardName  = (card.dataset.name || '').toLowerCase();

    let visible = true;
    if (category && cardCat !== category.toLowerCase()) visible = false;
    if (foodType && cardType !== foodType) visible = false;
    if (spiceLevel && cardSpice !== spiceLevel) visible = false;
    if (search && !cardName.includes(search)) visible = false;

    card.style.display = visible ? '' : 'none';
  });
}

function filterMenuItems(category) {
  applyAllFilters();
}

// ── Time Slot Picker (Reservations) ───────────────────────────────────────────
function initTimePicker() {
  const timeInput  = $('[name="time"]');
  const timeSlots  = $$('.time-slot');

  if (!timeSlots.length || !timeInput) return;

  timeSlots.forEach(slot => {
    slot.addEventListener('click', () => {
      if (slot.classList.contains('unavailable')) return;
      timeSlots.forEach(s => s.classList.remove('selected'));
      slot.classList.add('selected');
      timeInput.value = slot.dataset.time;
    });
  });

  // Check availability on date change
  const dateInput   = $('[name="date"]');
  const guestsInput = $('[name="guests"]');

  async function checkAvailability() {
    const date   = dateInput?.value;
    const guests = guestsInput?.value || 1;
    if (!date) return;

    const data = await apiFetch(`/reservations/check-availability?date=${date}&guests=${guests}`);
    if (!data.available_slots) return;

    timeSlots.forEach(slot => {
      const t = slot.dataset.time;
      if (data.available_slots.includes(t)) {
        slot.classList.remove('unavailable');
      } else {
        slot.classList.add('unavailable');
        if (slot.classList.contains('selected')) {
          slot.classList.remove('selected');
          timeInput.value = '';
        }
      }
    });
  }

  dateInput?.addEventListener('change', checkAvailability);
  guestsInput?.addEventListener('change', checkAvailability);
}

// ── Admin Toggles ─────────────────────────────────────────────────────────────
function initAdminToggles() {
  // Availability toggle
  $$('[data-toggle-availability]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const itemId = btn.dataset.toggleAvailability;
      const data = await apiFetch(`/admin/menu/${itemId}/toggle-availability`, { method: 'POST' });
      if (data.success) {
        showToast(data.message, 'success');
        const statusEl = $(`[data-availability-status="${itemId}"]`);
        if (statusEl) {
          statusEl.textContent = data.is_available ? 'Available' : 'Unavailable';
          statusEl.className = `status-badge status-badge--${data.is_available ? 'confirmed' : 'cancelled'}`;
        }
      }
    });
  });

  // Rule toggle
  $$('[data-toggle-rule]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const ruleId = btn.dataset.toggleRule;
      const data = await apiFetch(`/admin/rules/${ruleId}/toggle`, { method: 'POST' });
      if (data.success) {
        showToast(data.message, 'success');
        location.reload();
      }
    });
  });

  // Order status update
  $$('[data-update-order-status]').forEach(sel => {
    sel.addEventListener('change', async () => {
      const orderId   = sel.dataset.updateOrderStatus;
      const newStatus = sel.value;
      const data = await apiFetch(`/admin/orders/${orderId}/update-status`, {
        method: 'POST',
        body: JSON.stringify({ status: newStatus }),
      });
      if (data.success) {
        showToast(`Order status updated to ${newStatus}`, 'success');
      }
    });
  });
}

// ── Scroll Animations ─────────────────────────────────────────────────────────
function initScrollAnimations() {
  const elements = $$('[data-animate]');
  if (!elements.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animated');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

  elements.forEach(el => observer.observe(el));
}

// ── Recommendation Form ────────────────────────────────────────────────────────
function initRecommendationForm() {
  const form = $('#rec-form');
  if (!form) return;

  // Highlight selected radio/select options visually
  $$('.rec-option-group input[type="radio"]').forEach(radio => {
    radio.addEventListener('change', () => {
      const group = radio.name;
      $$(`input[name="${group}"]`).forEach(r => {
        r.closest('.rec-option')?.classList.remove('selected');
      });
      radio.closest('.rec-option')?.classList.add('selected');
    });
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initCart();
  initCartPage();
  initFlashMessages();
  initMenuFilters();
  initTimePicker();
  initAdminToggles();
  initScrollAnimations();
  initRecommendationForm();
});
