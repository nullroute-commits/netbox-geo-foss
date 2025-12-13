/**
 * K6 Load Test Script for Enterprise Application
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const loginSuccess = new Rate('login_success');
const apiSuccess = new Rate('api_success');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up to 10 users
    { duration: '5m', target: 50 },   // Ramp up to 50 users
    { duration: '10m', target: 100 }, // Stay at 100 users
    { duration: '5m', target: 50 },   // Ramp down to 50 users
    { duration: '2m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    errors: ['rate<0.1'],             // Error rate must be below 10%
    login_success: ['rate>0.9'],      // Login success rate must be above 90%
    api_success: ['rate>0.95'],       // API success rate must be above 95%
  },
};

// Test data
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TEST_USER = {
  email: `user${Math.random()}@test.com`,
  password: 'testpassword123',
  full_name: 'Load Test User',
};

// Helper function to check response
function checkResponse(response, expectedStatus = 200) {
  const success = check(response, {
    'status is correct': (r) => r.status === expectedStatus,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  errorRate.add(!success);
  return success;
}

// Setup: Create test user
export function setup() {
  const registerResponse = http.post(
    `${BASE_URL}/api/v1/auth/register`,
    JSON.stringify(TEST_USER),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  if (!checkResponse(registerResponse, 201)) {
    throw new Error('Failed to create test user');
  }
  
  return { user: TEST_USER };
}

// Main test scenario
export default function (data) {
  // 1. Login
  const loginResponse = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    `username=${data.user.email}&password=${data.user.password}`,
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
  );
  
  const loginOk = checkResponse(loginResponse);
  loginSuccess.add(loginOk);
  
  if (!loginOk) {
    return;
  }
  
  const token = JSON.parse(loginResponse.body).access_token;
  const authHeaders = {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  };
  
  // 2. Get user profile
  const profileResponse = http.get(`${BASE_URL}/api/v1/users/me`, authHeaders);
  const profileOk = checkResponse(profileResponse);
  apiSuccess.add(profileOk);
  
  sleep(1);
  
  // 3. List items (paginated)
  const listResponse = http.get(`${BASE_URL}/api/v1/items?limit=10&offset=0`, authHeaders);
  const listOk = checkResponse(listResponse);
  apiSuccess.add(listOk);
  
  sleep(0.5);
  
  // 4. Create an item
  const createItemResponse = http.post(
    `${BASE_URL}/api/v1/items`,
    JSON.stringify({
      name: `Test Item ${Date.now()}`,
      description: 'Load test item',
      price: Math.random() * 100,
    }),
    authHeaders
  );
  const createOk = checkResponse(createItemResponse, 201);
  apiSuccess.add(createOk);
  
  if (createOk) {
    const itemId = JSON.parse(createItemResponse.body).id;
    
    sleep(0.5);
    
    // 5. Get item details
    const getItemResponse = http.get(`${BASE_URL}/api/v1/items/${itemId}`, authHeaders);
    const getItemOk = checkResponse(getItemResponse);
    apiSuccess.add(getItemOk);
    
    sleep(0.5);
    
    // 6. Update item
    const updateItemResponse = http.put(
      `${BASE_URL}/api/v1/items/${itemId}`,
      JSON.stringify({
        name: `Updated Item ${Date.now()}`,
        price: Math.random() * 200,
      }),
      authHeaders
    );
    const updateOk = checkResponse(updateItemResponse);
    apiSuccess.add(updateOk);
    
    sleep(0.5);
    
    // 7. Delete item
    const deleteItemResponse = http.del(`${BASE_URL}/api/v1/items/${itemId}`, null, authHeaders);
    const deleteOk = checkResponse(deleteItemResponse, 204);
    apiSuccess.add(deleteOk);
  }
  
  sleep(2);
  
  // 8. Search
  const searchResponse = http.get(`${BASE_URL}/api/v1/search?q=test`, authHeaders);
  const searchOk = checkResponse(searchResponse);
  apiSuccess.add(searchOk);
  
  sleep(1);
  
  // 9. Health check (no auth required)
  const healthResponse = http.get(`${BASE_URL}/health`);
  checkResponse(healthResponse);
  
  sleep(3);
}

// Teardown: Cleanup
export function teardown(data) {
  // In a real scenario, you might want to delete the test user
  // For now, we'll just log completion
  console.log('Load test completed');
}