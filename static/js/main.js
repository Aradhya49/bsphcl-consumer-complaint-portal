// BSPHCL Portal – main.js

// Auto-dismiss alert messages
document.addEventListener('DOMContentLoaded', function () {

  // Close button for alerts
  document.querySelectorAll('.xbtn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      this.closest('.alert').remove();
    });
  });

  // Auto-hide alerts after 6 seconds
  setTimeout(function () {
    document.querySelectorAll('.alert').forEach(function (el) {
      el.style.transition = 'opacity 0.5s';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 500);
    });
  }, 6000);

  // Complaint form: show subcategory based on complaint type
  var typeSelect = document.getElementById('complaint_type');
  var subSelect  = document.getElementById('subcategory');

  var subcategories = {
    'Billing Issue':       ['Incorrect meter reading', 'Wrong bill amount', 'Duplicate bill', 'Bill not received', 'Other billing issue'],
    'Power Outage':        ['Transformer failure', 'Area blackout', 'Voltage fluctuation', 'Frequent power cuts', 'Other outage'],
    'Meter Problem':       ['Meter not working', 'Meter tampered', 'Meter burning', 'Meter running fast', 'Other meter issue'],
    'Connection Request':  ['New connection', 'Temporary connection', 'Change of load', 'Disconnection request', 'Reconnection request'],
    'Others':              ['General query', 'Staff behaviour', 'Pole / wire issue', 'Other']
  };

  if (typeSelect && subSelect) {
    function populateSub(val) {
      subSelect.innerHTML = '<option value="">-- Select Subcategory --</option>';
      if (val && subcategories[val]) {
        subcategories[val].forEach(function (s) {
          var opt = document.createElement('option');
          opt.value = s; opt.textContent = s;
          subSelect.appendChild(opt);
        });
        subSelect.closest('.fg').style.display = 'block';
      } else {
        subSelect.closest('.fg').style.display = 'none';
      }
    }
    typeSelect.addEventListener('change', function () { populateSub(this.value); });
    // On page load if value already set
    if (typeSelect.value) populateSub(typeSelect.value);
    else subSelect.closest('.fg').style.display = 'none';
  }

  // Confirm before delete actions
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(this.dataset.confirm || 'Are you sure?')) {
        e.preventDefault();
      }
    });
  });

  // File input: show selected filename
  document.querySelectorAll('input[type="file"]').forEach(function (inp) {
    inp.addEventListener('change', function () {
      var label = document.getElementById('file-label');
      if (label) {
        label.textContent = this.files.length ? this.files[0].name : 'No file chosen';
      }
    });
  });

});
