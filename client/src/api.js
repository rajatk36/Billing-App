import { getAuth } from 'firebase/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Helper to get current Firebase ID token
  async getIdToken() {
    const auth = getAuth();
    const user = auth.currentUser;
    if (!user) return null;
    return await user.getIdToken();
  }

  // Helper method to make API calls
  async makeRequest(endpoint, options = {}) {
  const url = `${this.baseURL}${endpoint}`;
  const token = await this.getIdToken();

  // Merge headers safely
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  // Ensure method defaults to GET
  const method = options.method || 'GET';

  // Prepare fetch config (avoid double-stringifying bodies)
  const config = {
    method,
    headers,
    body: options.body !== undefined
      ? (typeof options.body === 'string' ? options.body : JSON.stringify(options.body))
      : undefined,
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errText}`);
    }
    // Return JSON only if response has content
    if (response.status !== 204) {
      return await response.json();
    }
    return {};
  } catch (error) {
    console.error("API Request failed:", error);
    throw error;
  }
}



  // Authentication methods (handled by Firebase on client generally)
  async signup(email, password) {
    return this.makeRequest('/signup', {
      method: 'POST',
      body: { email, password },
    });
  }

  async login(email, password) {
    return this.makeRequest('/login', {
      method: 'POST',
      body: { email, password },
    });
  }

  async logout() {
    return this.makeRequest('/logout', {
      method: 'POST',
    });
  }

  async checkAuth() {
    return this.makeRequest('/check-auth');
  }

  // Billing methods
  async getBills() {
    return this.makeRequest('/get_bills');
  }

  async addBill(billData) {
    return this.makeRequest('/add_bill', {
      method: 'POST',
      body: billData,
    });
  }

  async updateBill(billId, billData) {
    return this.makeRequest(`/update_bill/${billId}`, {
      method: 'PUT',
      body: billData,
    });
  }

  async deleteBill(billId) {
    return this.makeRequest(`/delete_bill/${billId}`, {
      method: 'DELETE',
    });
  }

  // User statistics
  async getUserStats() {
    return this.makeRequest('/user-stats');
  }

  // Admin methods
  async viewAllUsersData() {
    return this.makeRequest('/admin/view-all-data');
  }
  async deleteAccount() {
    return this.makeRequest('/delete-account', {
      method: 'DELETE',
    });
  }
}

export default new ApiService();
