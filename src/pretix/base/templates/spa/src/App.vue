<template>
  <div id="app">
    <!-- Your main app content -->
    <router-view />
    
    <!-- Add CSRF token meta tag for compatibility -->
    <meta name="csrf-token" :content="csrfToken" />
  </div>
</template>

<script>
import ErrorService from './services/ErrorService.js'

export default {
  name: 'App',
  data() {
    return {
      csrfToken: '',
      errorService: null
    }
  },
  async created() {
    // Initialize error service
    this.errorService = new ErrorService(this.$router);
    
    // Get CSRF token
    this.csrfToken = this.getCSRFToken();
    
    // Set up global error handling
    this.setupGlobalErrorHandling();
  },
  methods: {
    getCSRFToken() {
      // Try to get CSRF token from various sources
      return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
             this.getCookie('csrftoken') ||
             '';
    },
    
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
    },
    
    setupGlobalErrorHandling() {
      // Handle window errors
      window.addEventListener('error', (event) => {
        console.error('Global error:', event.error);
        this.errorService.showError('500', {
          exception: event.error.message
        });
      });
      
      // You can also provide the error service globally
      this.$root.errorService = this.errorService;
    }
  }
}
</script>

<style>
/* Your existing app styles */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Import FontAwesome for icons (same as Django templates) */
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css');
</style>