// Debug Login Component
// Run this in browser console to check login component status

console.log('=== LOGIN COMPONENT DEBUG ===');

// Check if React is loaded
if (typeof React !== 'undefined') {
  console.log('✅ React is loaded');
} else {
  console.log('❌ React is not loaded');
}

// Check if the login container exists
const loginContainer = document.querySelector('.login-new-container');
if (loginContainer) {
  console.log('✅ Login container found');
  console.log('Classes:', loginContainer.className);
  console.log('Opacity:', window.getComputedStyle(loginContainer).opacity);
  console.log('Visibility:', window.getComputedStyle(loginContainer).visibility);
  console.log('Display:', window.getComputedStyle(loginContainer).display);
} else {
  console.log('❌ Login container not found');
}

// Check if the login card exists
const loginCard = document.querySelector('.login-new-card');
if (loginCard) {
  console.log('✅ Login card found');
  console.log('Classes:', loginCard.className);
} else {
  console.log('❌ Login card not found');
}

// Check for any JavaScript errors
window.addEventListener('error', function(e) {
  console.log('❌ JavaScript Error:', e.message);
  console.log('File:', e.filename);
  console.log('Line:', e.lineno);
});

// Check if the component is visible
setTimeout(() => {
  const container = document.querySelector('.login-new-container');
  if (container) {
    const opacity = window.getComputedStyle(container).opacity;
    const transform = window.getComputedStyle(container).transform;
    console.log('After 1 second:');
    console.log('Opacity:', opacity);
    console.log('Transform:', transform);
    
    if (opacity === '0') {
      console.log('❌ Component is still invisible - opacity is 0');
    } else {
      console.log('✅ Component should be visible');
    }
  }
}, 1000);

console.log('=== END DEBUG ==='); 