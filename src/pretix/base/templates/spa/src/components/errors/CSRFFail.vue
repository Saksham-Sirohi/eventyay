<template>
  <BaseError>
    <i class="fa fa-frown-o big-icon fa-fw"></i>
    <div class="error-details">
      <h1>{{ $t('Verification failed') }}</h1>
      <p>{{ $t('We could not verify that this request really was sent from you. For security reasons, we therefore cannot process it.') }}</p>
      
      <p v-if="noReferer">{{ noReferer1 }}</p>
      <p v-if="noReferer">{{ noReferer2 }}</p>
      
      <p v-else-if="noCookie">{{ noCookie1 }}</p>
      <p v-else-if="noCookie">{{ noCookie2 }}</p>
      
      <p v-else>{{ $t('Please go back to the last page, refresh this page and then try again. If the problem persists, please get in touch with us.') }}</p>
      
      <p class="links">
        <a id="goback" href="#">{{ $t('Take a step back') }}</a>
      </p>
      <img src="../../../static/pretixbase/img/eventyay-logo.svg" class="logo" alt="Eventyay Logo" />
    </div>
  </BaseError>
</template>

<script>
import BaseError from './BaseError.vue';

export default {
  name: 'CSRFFail',
  components: {
    BaseError
  },
  props: {
    reason: {
      type: String,
      default: ''
    },
    noReferer: {
      type: Boolean,
      default: false
    },
    noCookie: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    noReferer1() {
      return this.$t('You are seeing this message because this HTTPS site requires a \'Referer header\' to be sent by your Web browser, but none was sent. This header is required for security reasons, to ensure that your browser is not being hijacked by third parties.');
    },
    noReferer2() {
      return this.$t('If you have configured your browser to disable \'Referer\' headers, please re-enable them, at least for this site, or for HTTPS connections, or for \'same-origin\' requests.');
    },
    noCookie1() {
      return this.$t('You are seeing this message because this site requires a CSRF cookie when submitting forms. This cookie is required for security reasons, to ensure that your browser is not being hijacked by third parties.');
    },
    noCookie2() {
      return this.$t('If you have configured your browser to disable cookies, please re-enable them, at least for this site, or for \'same-origin\' requests.');
    }
  },
  head() {
    return {
      title: this.$t('Verification failed')
    };
  }
}
</script>