import { createClient } from '@base44/sdk';
// import { getAccessToken } from '@base44/sdk/utils/auth-utils';

// Create a client with authentication required
export const base44 = createClient({
  appId: "684354711db42f36f3af4a96", 
  requiresAuth: true // Ensure authentication is required for all operations
});
