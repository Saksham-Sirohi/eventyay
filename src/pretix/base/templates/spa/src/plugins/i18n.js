// i18n.js - Vue.js internationalization plugin to replace Django's i18n
export default {
  install(app, options = {}) {
    const translations = options.translations || {};
    const defaultLocale = options.defaultLocale || 'en';
    
    // Simple translation function
    const $t = (key, params = {}) => {
      const locale = getCurrentLocale();
      const translation = translations[locale]?.[key] || translations[defaultLocale]?.[key] || key;
      
      // Simple parameter replacement
      return Object.keys(params).reduce((str, param) => {
        return str.replace(new RegExp(`{${param}}`, 'g'), params[param]);
      }, translation);
    };
    
    // Get current locale (could be enhanced to read from localStorage, URL, etc.)
    const getCurrentLocale = () => {
      return localStorage.getItem('locale') || 
             navigator.language.split('-')[0] || 
             defaultLocale;
    };
    
    // Format date similar to Django's date_format
    const formatDate = (date, format = 'SHORT_DATE_FORMAT') => {
      const d = new Date(date);
      const locale = getCurrentLocale();
      
      const formats = {
        'SHORT_DATE_FORMAT': { 
          year: 'numeric', 
          month: 'short', 
          day: 'numeric' 
        },
        'SHORT_DATETIME_FORMAT': { 
          year: 'numeric', 
          month: 'short', 
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        }
      };
      
      return d.toLocaleDateString(locale, formats[format] || formats['SHORT_DATE_FORMAT']);
    };
    
    // Format currency similar to Django's money_filter
    const formatCurrency = (value, currency = 'USD') => {
      const locale = getCurrentLocale();
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency
      }).format(value);
    };
    
    // Format number similar to Django's number_format
    const formatNumber = (value, decimalPos = 2) => {
      const locale = getCurrentLocale();
      return new Intl.NumberFormat(locale, {
        minimumFractionDigits: decimalPos,
        maximumFractionDigits: decimalPos
      }).format(value);
    };
    
    // Make available globally
    app.config.globalProperties.$t = $t;
    app.config.globalProperties.$formatDate = formatDate;
    app.config.globalProperties.$formatCurrency = formatCurrency;
    app.config.globalProperties.$formatNumber = formatNumber;
    
    // Provide for composition API
    app.provide('$t', $t);
    app.provide('$formatDate', formatDate);
    app.provide('$formatCurrency', formatCurrency);
    app.provide('$formatNumber', formatNumber);
  }
};

// Default translations (you would expand this)
export const defaultTranslations = {
  en: {
    'Bad Request': 'Bad Request',
    'We were unable to parse your request.': 'We were unable to parse your request.',
    'Take a step back': 'Take a step back',
    'Try again': 'Try again',
    'Permission denied': 'Permission denied',
    'You do not have access to this page.': 'You do not have access to this page.',
    'Admin mode': 'Admin mode',
    'Not found': 'Not found',
    "I'm afraid we could not find the the resource you requested.": "I'm afraid we could not find the the resource you requested.",
    'Internal Server Error': 'Internal Server Error',
    'We had trouble processing your request.': 'We had trouble processing your request.',
    'If this problem persists, please contact us.': 'If this problem persists, please contact us.',
    'If you contact us, please send us the following code:': 'If you contact us, please send us the following code:',
    'Verification failed': 'Verification failed',
    'We could not verify that this request really was sent from you. For security reasons, we therefore cannot process it.': 'We could not verify that this request really was sent from you. For security reasons, we therefore cannot process it.',
    'Please go back to the last page, refresh this page and then try again. If the problem persists, please get in touch with us.': 'Please go back to the last page, refresh this page and then try again. If the problem persists, please get in touch with us.',
    'You are seeing this message because this HTTPS site requires a \'Referer header\' to be sent by your Web browser, but none was sent. This header is required for security reasons, to ensure that your browser is not being hijacked by third parties.': 'You are seeing this message because this HTTPS site requires a \'Referer header\' to be sent by your Web browser, but none was sent. This header is required for security reasons, to ensure that your browser is not being hijacked by third parties.',
    'If you have configured your browser to disable \'Referer\' headers, please re-enable them, at least for this site, or for HTTPS connections, or for \'same-origin\' requests.': 'If you have configured your browser to disable \'Referer\' headers, please re-enable them, at least for this site, or for HTTPS connections, or for \'same-origin\' requests.',
    'You are seeing this message because this site requires a CSRF cookie when submitting forms. This cookie is required for security reasons, to ensure that your browser is not being hijacked by third parties.': 'You are seeing this message because this site requires a CSRF cookie when submitting forms. This cookie is required for security reasons, to ensure that your browser is not being hijacked by third parties.',
    'If you have configured your browser to disable cookies, please re-enable them, at least for this site, or for \'same-origin\' requests.': 'If you have configured your browser to disable cookies, please re-enable them, at least for this site, or for \'same-origin\' requests.',
  }
  // Add other languages as needed
};