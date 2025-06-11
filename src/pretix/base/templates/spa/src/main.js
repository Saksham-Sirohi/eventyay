import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import i18nPlugin, { defaultTranslations } from './plugins/i18n.js'

// Import error components globally
import BaseError from './components/errors/BaseError.vue'
import Error400 from './components/errors/Error400.vue'
import Error403 from './components/errors/Error403.vue'
import Error404 from './components/errors/Error404.vue'
import Error500 from './components/errors/Error500.vue'
import CSRFFail from './components/errors/CSRFFail.vue'

const app = createApp(App)

// Add error handling
app.config.errorHandler = (error, instance, info) => {
  console.error('Vue error:', error, info);
  
  // You can customize error handling here
  // For example, show a 500 error component
  if (router.currentRoute.value.name !== 'error-500') {
    router.push({
      name: 'error-500',
      params: {
        exception: error.message
      }
    });
  }
};

// Register global error components
app.component('BaseError', BaseError)
app.component('Error400', Error400)
app.component('Error403', Error403)
app.component('Error404', Error404)
app.component('Error500', Error500)
app.component('CSRFFail', CSRFFail)

// Add i18n plugin
app.use(i18nPlugin, {
  translations: defaultTranslations,
  defaultLocale: 'en'
})

app.use(createPinia())
app.use(router)

// Handle uncaught promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  
  // Handle specific error types
  if (event.reason?.response?.status === 403) {
    router.push({
      name: 'error-403',
      params: {
        exception: event.reason.message
      }
    });
  } else if (event.reason?.response?.status === 404) {
    router.push({
      name: 'error-404',
      params: {
        exception: event.reason.message
      }
    });
  } else if (event.reason?.response?.status >= 500) {
    router.push({
      name: 'error-500',
      params: {
        exception: event.reason.message
      }
    });
  }
});

app.mount('#app')