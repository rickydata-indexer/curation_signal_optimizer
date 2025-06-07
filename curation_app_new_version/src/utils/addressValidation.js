// Ethereum address validation utilities

// Check if address is a valid Ethereum address format
export function isValidEthereumAddress(address) {
  if (!address) return false;
  
  // Check if it's a valid hex string with 0x prefix and 40 hex characters
  const ethAddressRegex = /^0x[a-fA-F0-9]{40}$/;
  return ethAddressRegex.test(address);
}

// Normalize address to lowercase with 0x prefix
export function normalizeAddress(address) {
  if (!address) return '';
  
  // Remove any whitespace
  const trimmed = address.trim();
  
  // Add 0x prefix if missing
  const withPrefix = trimmed.startsWith('0x') ? trimmed : `0x${trimmed}`;
  
  // Convert to lowercase
  return withPrefix.toLowerCase();
}

// Validate and normalize address
export function validateAndNormalizeAddress(address) {
  if (!address) {
    return { isValid: false, normalized: '', error: 'Address is required' };
  }
  
  const normalized = normalizeAddress(address);
  
  if (!isValidEthereumAddress(normalized)) {
    return { 
      isValid: false, 
      normalized: '', 
      error: 'Invalid Ethereum address format. Must be 40 hex characters with 0x prefix.' 
    };
  }
  
  return { isValid: true, normalized, error: null };
} 