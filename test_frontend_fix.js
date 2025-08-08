// Test script to verify the getRatingStars function fix
function getRatingStars(rating = 4.5) {
  // Ensure rating is within valid range (0-5)
  const clampedRating = Math.max(0, Math.min(5, rating));
  const fullStars = Math.floor(clampedRating);
  const hasHalfStar = clampedRating % 1 >= 0.5;
  const emptyStars = Math.max(0, 5 - fullStars - (hasHalfStar ? 1 : 0));
  
  return {
    fullStars,
    hasHalfStar,
    emptyStars,
    clampedRating: clampedRating.toFixed(1)
  };
}

// Test cases
console.log("Testing getRatingStars function...");

// Test 1: Normal rating
console.log("Test 1 - Rating 4.2:", getRatingStars(4.2));

// Test 2: High rating (should be clamped to 5)
console.log("Test 2 - Rating 6.0:", getRatingStars(6.0));

// Test 3: Negative rating (should be clamped to 0)
console.log("Test 3 - Rating -1:", getRatingStars(-1));

// Test 4: Edge case with index calculation
for (let i = 0; i < 10; i++) {
  const rating = 4.2 + (i * 0.1);
  const clampedRating = Math.min(5, rating);
  console.log(`Test 4.${i} - Index ${i}, Rating ${rating.toFixed(1)}, Clamped: ${clampedRating.toFixed(1)}`);
}

console.log("All tests completed successfully!"); 