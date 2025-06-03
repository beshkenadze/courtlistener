// File: sdk/courtlistener-api/custom-instance.ts

// --- Test Configuration ---
// In a real setup, these would come from environment variables or a proper test setup file.
// TEST_BASE_URL should be just the scheme and hostname, e.g., http://localhost:8000
// Orval's `baseUrl` in the config usually handles the /api/rest/v4 part, so the `url`
// parameter received by this function will already be prefixed with that.
// However, for direct testing of customInstance or if baseUrl is not used in orval config,
// you might need to adjust. The Orval config *does* set baseUrl: '/api/rest/v4'.
// So, the `url` argument to this function will be like `/api/rest/v4/dockets/`.
// Thus, TEST_BASE_URL should be the actual scheme+host.
const TEST_BASE_URL = 'http://localhost:8000'; // Example: Django's default dev server
const API_TOKEN = 'your_test_api_token_here'; // Replace with a real test token if available for actual testing

export const customInstance = async <T>(
  url: string, // This 'url' from Orval will be like /api/rest/v4/dockets/
  config?: RequestInit
): Promise<T> => {
  // Construct full URL
  const fullUrl = `${TEST_BASE_URL}${url}`;

  const headers = new Headers(config?.headers);
  if (API_TOKEN && API_TOKEN !== 'your_test_api_token_here') { // Avoid sending placeholder token
    headers.set('Authorization', `Token ${API_TOKEN}`);
  }

  // Add a common header, e.g., Content-Type, if not already present
  if (!headers.has('Content-Type') && !(config?.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // Default method to GET if not specified
  const method = config?.method || 'GET';

  const response = await fetch(fullUrl, {
    ...config,
    method,
    headers,
  });

  if (!response.ok) {
    // Attempt to parse error response as JSON, otherwise use status text
    let errorData;
    try {
      errorData = await response.json();
    } catch (e) {
      errorData = { message: response.statusText };
    }
    throw new Error(errorData?.detail || errorData?.message || response.statusText);
  }

  if (response.status === 204) { // Handle No Content
    return undefined as T;
  }

  // Attempt to parse JSON, but handle cases where response might be empty or non-JSON
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    // To prevent errors with empty responses that still carry application/json
    const text = await response.text();
    if (text) {
      return JSON.parse(text);
    }
    return undefined as T; // Or handle as appropriate for your API
  }

  // For non-JSON responses, you might need to handle them differently.
  // This basic example just returns the response as is, which might not be what Orval expects.
  // Orval generated code usually expects a parsed JSON object.
  // If your API sometimes returns non-JSON successfully, this part needs more robust handling.
  // For now, we assume successful non-JSON responses are not typical for this SDK.
  // Returning response.text() might be a safer default if non-JSON is possible.
  // However, Orval's default fetch client might implicitly expect JSON.
  // Let's stick to trying JSON for now, as per typical Orval usage.
  // If this line is reached, it means content-type was not application/json or was null
  // and it wasn't a 204. This could be an issue.
  // For a robust SDK, ensure all valid response types are handled.
  // For testing, this might highlight endpoints not returning JSON as expected.
  return response.json();
};

export default customInstance;
