<template>
  <div class="container">
    <slot />
  </div>
</template>

<script>
export default {
  name: 'BaseError',
  mounted() {
    // Load the errors.js script functionality
    this.initializeErrorHandlers();
  },
  methods: {
    initializeErrorHandlers() {
      // Replicate the functionality from pretixbase/js/errors.js
      const gobackButton = document.getElementById('goback');
      const reloadButton = document.getElementById('reload');
      
      if (gobackButton) {
        gobackButton.addEventListener('click', (e) => {
          e.preventDefault();
          window.history.back();
        });
      }
      
      if (reloadButton) {
        reloadButton.addEventListener('click', (e) => {
          e.preventDefault();
          window.location.reload();
        });
      }
    }
  }
}
</script>

<style>
/* Import the same CSS that Django uses */
@import '../../../static/pretixbase/scss/error.scss';
</style>