import { createRouter, createWebHistory } from 'vue-router'

// Import error components
import Error400 from '../components/errors/Error400.vue'
import Error403 from '../components/errors/Error403.vue'
import Error404 from '../components/errors/Error404.vue'
import Error500 from '../components/errors/Error500.vue'
import CSRFFail from '../components/errors/CSRFFail.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/error/400',
      name: 'error-400',
      component: Error400,
      props: route => ({
        exception: route.params.exception || route.query.exception || ''
      })
    },
    {
      path: '/error/403',
      name: 'error-403',
      component: Error403,
      props: route => ({
        exception: route.params.exception || route.query.exception || '',
        isStaff: route.params.isStaff || route.query.isStaff === 'true' || false,
        staffSession: route.params.staffSession || route.query.staffSession === 'true' || false,
        csrfToken: route.params.csrfToken || route.query.csrfToken || ''
      })
    },
    {
      path: '/error/404',
      name: 'error-404',
      component: Error404,
      props: route => ({
        exception: route.params.exception || route.query.exception || '',
        isStaff: route.params.isStaff || route.query.isStaff === 'true' || false,
        staffSession: route.params.staffSession || route.query.staffSession === 'true' || false,
        csrfToken: route.params.csrfToken || route.query.csrfToken || ''
      })
    },
    {
      path: '/error/500',
      name: 'error-500',
      component: Error500,
      props: route => ({
        exception: route.params.exception || route.query.exception || '',
        sentryEventId: route.params.sentryEventId || route.query.sentryEventId || ''
      })
    },
    {
      path: '/error/csrf',
      name: 'error-csrf',
      component: CSRFFail,
      props: route => ({
        reason: route.params.reason || route.query.reason || '',
        noReferer: route.params.noReferer === 'true' || route.query.noReferer === 'true' || false,
        noCookie: route.params.noCookie === 'true' || route.query.noCookie === 'true' || false
      })
    },
    // Catch-all 404 route - should be last
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: Error404,
      props: {
        exception: 'Page not found'
      }
    }
  ],
})

// Global navigation guard for error handling
router.beforeEach((to, from, next) => {
  // You can add authentication checks here
  // and redirect to appropriate error pages
  
  next()
})

// Handle route errors
router.onError((error) => {
  console.error('Router error:', error);
  
  // Navigate to appropriate error page based on error type
  if (error.message.includes('403')) {
    router.push('/error/403');
  } else if (error.message.includes('404')) {
    router.push('/error/404');
  } else {
    router.push('/error/500');
  }
})

export default router