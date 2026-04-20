// Seam — main.js

// Auto-dismiss flash messages after 4 seconds
document.querySelectorAll('.flash').forEach(function(el) {
  setTimeout(function() {
    el.style.transition = 'opacity 0.4s';
    el.style.opacity = '0';
    setTimeout(function() { el.remove(); }, 400);
  }, 4000);
});

// Show selected filename on photo upload inputs
document.querySelectorAll('.photo-upload__input').forEach(function(input) {
  input.addEventListener('change', function() {
    var label = input.nextElementSibling;
    if (!label) return;
    var count = input.files.length;
    if (count === 0) {
      label.textContent = 'Tap to add a photo';
    } else if (count === 1) {
      label.textContent = input.files[0].name;
    } else {
      label.textContent = count + ' photos selected';
    }
  });
});
