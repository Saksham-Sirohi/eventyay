// ErrorService.js - Service to handle errors similar to Django's error handling
import axios from 'axios'

class ErrorService {
  constructor(router) {
    this.router = router;
    this.setupAxiosInterceptors();
  }

  setupAxiosInterceptors() {
    // Request interceptor to add CSRF token
    axios.interceptors.request.use((config) => {
      const csrfToken = this.getCSRFToken();
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
      return config;
    }, (error) => {
      return Promise.reject(error);
    });

    // Response interceptor to handle errors
    axios.interceptors.response.use(
      (response) => response,
      (error) => {
        this.handleError(error);
        return Promise.reject(error);
      }
    );
  }

  getCSRFToken() {
    // Get CSRF token from cookie or meta tag
    const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                  this.getCookie('csrftoken');
    return token;
  }

  getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  handleError(error) {
    if (!error.response) {
      // Network error
      this.router.push({
        name: 'error-500',
        params: {
          exception: 'Network error: Unable to connect to server'
        }
      });
      return;
    }

    const status = error.response.status;
    const data = error.response.data;

    switch (status) {
      case 400:
        this.router.push({
          name: 'error-400',
          params: {
            exception: data.detail || data.message || 'Bad Request'
          }
        });
        break;

      case 403:
        // Check if it's a CSRF error
        if (data.detail && data.detail.includes('CSRF')) {
          this.router.push({
            name: 'error-csrf',
            params: {
              reason: data.reason || '',
              noReferer: data.reason === 'REASON_NO_REFERER',
              noCookie: data.reason === 'REASON_NO_CSRF_COOKIE'
            }
          });
        } else {
          this.router.push({
            name: 'error-403',
            params: {
              exception: data.detail || data.message || 'Permission denied'
            }
          });
        }
        break;

      case 404:
        this.router.push({
          name: 'error-404',
          params: {
            exception: data.detail || data.message || 'Not found'
          }
        });
        break;

      case 500:
      default:
        this.router.push({
          name: 'error-500',
          params: {
            exception: data.detail || data.message || 'Internal server error',
            sentryEventId: data.sentry_event_id || ''
          }
        });
        break;
    }
  }

  // Method to show error programmatically
  showError(statusCode, options = {}) {
    const routeMap = {
      '400': 'error-400',
      '403': 'error-403', 
      '404': 'error-404',
      '500': 'error-500',
      'csrf': 'error-csrf'
    };

    const routeName = routeMap[statusCode];
    if (routeName) {
      this.router.push({
        name: routeName,
        params: options
      });
    }
  }
}

// Export the class as default
export default ErrorService;