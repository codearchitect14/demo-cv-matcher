// Debug Authentication Script
// Run this in browser console to check authentication status

console.log('=== AUTHENTICATION DEBUG ===');

// Check all possible token storage locations
const tokenLocations = {
  'localStorage.access_token': localStorage.getItem('access_token'),
  'localStorage.token': localStorage.getItem('token'),
  'localStorage.recruiterToken': localStorage.getItem('recruiterToken'),
  'localStorage.candidateToken': localStorage.getItem('candidateToken'),
  'sessionStorage.access_token': sessionStorage.getItem('access_token'),
  'sessionStorage.token': sessionStorage.getItem('token'),
  'sessionStorage.recruiterToken': sessionStorage.getItem('recruiterToken'),
  'sessionStorage.candidateToken': sessionStorage.getItem('candidateToken')
};

console.log('Token Storage Status:');
Object.entries(tokenLocations).forEach(([key, value]) => {
  console.log(`${key}: ${value ? '✅ Found' : '❌ Not found'}`);
  if (value) {
    console.log(`  Length: ${value.length}`);
    console.log(`  Preview: ${value.substring(0, 20)}...`);
  }
});

// Check if any token exists
const hasAnyToken = Object.values(tokenLocations).some(token => token);
console.log(`\nHas any token: ${hasAnyToken ? '✅ Yes' : '❌ No'}`);

// Test API call if token exists
if (hasAnyToken) {
  console.log('\nTesting API call...');
  const token = tokenLocations['localStorage.access_token'] || 
                tokenLocations['localStorage.token'] ||
                tokenLocations['sessionStorage.access_token'] ||
                tokenLocations['sessionStorage.token'];
  
  if (token) {
    fetch('http://localhost:8000/api/v1/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    .then(response => {
      console.log(`API Response Status: ${response.status}`);
      if (response.ok) {
        return response.json();
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    })
    .then(data => {
      console.log('✅ API call successful:', data);
    })
    .catch(error => {
      console.log('❌ API call failed:', error.message);
    });
  }
}

// Check current page and navigation
console.log(`\nCurrent URL: ${window.location.href}`);
console.log(`Current pathname: ${window.location.pathname}`);

console.log('\n=== END DEBUG ==='); 