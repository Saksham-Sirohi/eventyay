<template>
  <BaseError>
    <i class="fa fa-frown-o fa-fw big-icon"></i>
    <div class="error-details">
      <h1>{{ $t('Bad Request') }}</h1>
      <p>{{ $t('We were unable to parse your request.') }}</p>
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
  name: 'Error400',
  components: {
    BaseError
  },
  props: {
    exception: {
      type: String,
      default: ''
    }
  },
  head() {
    return {
      title: this.$t('Bad Request')
    };
  }
}
</script>