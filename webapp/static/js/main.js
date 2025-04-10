// Main JavaScript for SCADA RFP Finder

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
  // Initialize Bootstrap tooltips
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
  });
  
  // Initialize Bootstrap popovers
  var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
  var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl)
  });
  
  // Fade out flash messages after 5 seconds
  setTimeout(function() {
    document.querySelectorAll('.alert').forEach(function(alert) {
      var bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 5000);
});

// Favorite toggle functionality
function toggleFavorite(rfpId, element) {
  fetch(`/rfps/${rfpId}/favorite`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.is_favorite) {
      element.classList.remove('far');
      element.classList.add('fas', 'active');
    } else {
      element.classList.remove('fas', 'active');
      element.classList.add('far');
    }
  })
  .catch(error => console.error('Error:', error));
}

// Format date helper
function formatDate(dateString) {
  if (!dateString) return 'Not specified';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

// Calculate days until due
function daysUntilDue(dueDateString) {
  if (!dueDateString) return null;
  
  const dueDate = new Date(dueDateString);
  const today = new Date();
  
  // Reset time part for accurate day calculation
  dueDate.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  
  const diffTime = dueDate - today;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  return diffDays;
}

// Format relevance score with appropriate color
function formatRelevanceScore(score) {
  let colorClass = '';
  
  if (score >= 80) {
    colorClass = 'text-success';
  } else if (score >= 50) {
    colorClass = 'text-warning';
  } else {
    colorClass = 'text-danger';
  }
  
  return `<span class="${colorClass}">${score}%</span>`;
}
