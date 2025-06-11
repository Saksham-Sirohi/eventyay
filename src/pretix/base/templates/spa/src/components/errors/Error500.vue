<template>
  <BaseError>
    <i class="fa fa-bolt big-icon fa-fw"></i>
    <div class="error-details">
      <h1>{{ $t('Internal Server Error') }}</h1>
      <p>{{ $t('We had trouble processing your request.') }}</p>
      <p>{{ $t('If this problem persists, please contact us.') }}</p>
      <p v-if="sentryEventId">
        {{ $t('If you contact us, please send us the following code:') }}
        <br>
        {{ sentryEventId }}
      </p>
      <p v-if="exception">{{ exception }}</p>
      <p class="links">
        <a id="goback" href="#">{{ $t('Take a step back') }}</a>
        &middot; <a id="reload" href="#">{{ $t('Try again') }}</a>
      </p>
      <img src="../../../static/pretixbase/img/eventyay-logo.svg" class="logo" alt="Eventyay Logo" />
    </div>
  </BaseError>
</template>

<script>
import BaseError from './BaseError.vue';

export default {
  name: 'Error500',
  components: {
    BaseError
  },
  props: {
    exception: {
      type: String,
      default: ''
    },
    sentryEventId: {
      type: String,
      default: ''
    }
  },
  head() {
    return {
      title: this.$t('Internal Server Error')
    };
  }
}
</script>