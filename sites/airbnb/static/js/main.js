// Airbnb mirror — small progressive enhancements. Every feature works without JS.
(function () {
  'use strict';

  // Close open header menus when clicking elsewhere or pressing Escape.
  function closeMenus(except) {
    document.querySelectorAll('details.user-menu[open]').forEach(function (d) {
      if (d !== except) d.removeAttribute('open');
    });
  }
  document.addEventListener('click', function (e) {
    var menu = e.target.closest('details.user-menu');
    closeMenus(menu);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeMenus(null);
  });

  // Payment step on the booking page: only require the new-card fields when
  // "Add a new card" is the selected payment method.
  var newCard = document.querySelector('.new-card');
  if (newCard) {
    var radios = document.querySelectorAll('input[name="payment_method"]');
    var sync = function () {
      var checked = document.querySelector('input[name="payment_method"]:checked');
      var isNew = checked && checked.value === 'new';
      newCard.hidden = !isNew;
      newCard.querySelectorAll('input, select').forEach(function (el) {
        if (el.dataset.required === '1') el.required = isNew;
      });
    };
    newCard.querySelectorAll('input[required], select[required]').forEach(function (el) {
      el.dataset.required = '1';
    });
    radios.forEach(function (r) { r.addEventListener('change', sync); });
    sync();
  }

  // Keep check-out after check-in in date inputs.
  document.querySelectorAll('input[name="checkin"], input[name="check_in"]').forEach(function (inp) {
    var form = inp.form;
    if (!form) return;
    var out = form.querySelector('input[name="checkout"], input[name="check_out"]');
    if (!out || inp.type !== 'date') return;
    inp.addEventListener('change', function () {
      if (inp.value) out.min = inp.value;
    });
  });

  // Dismiss flash messages on click.
  document.querySelectorAll('.flash-wrap .alert').forEach(function (el) {
    el.addEventListener('click', function () { el.remove(); });
  });
})();
