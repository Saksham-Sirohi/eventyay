<template>
  <BaseError>
    <i class="fa fa-meh-o fa-fw big-icon"></i>
    <div class="error-details">
      <h1>{{ $t('Not found') }}</h1>
      <p>{{ $t("I'm afraid we could not find the the resource you requested.") }}</p>
      <p v-if="exception">{{ exception }}</p>
      <p class="links">
        <a id="goback" href="#">{{ $t('Take a step back') }}</a>
      </p>
      <form 
        v-if="isStaff && !staffSession" 
        :action="`/control/user/sudo?next=${encodeURIComponent(currentPath + '?' + queryString)}`" 
        method="post"
      >
        <p>
          <input type="hidden" name="csrfmiddlewaretoken" :value="csrfToken" />
          <button type="submit" class="btn btn-default" id="button-sudo">
            <i class="fa fa-id-card"></i> {{ $t('Admin mode') }}
          </button>
        </p>
      </form>
      <img src="../../../static/pretixbase/img/eventyay-logo.svg" class="logo" alt="Eventyay Logo" />
    </div>
  </BaseError>
</template>

<script>
import BaseError from './BaseError.vue';

export default {
  name: 'Error404',
  components: {
    BaseError
  },
  props: {
    exception: {
      type: String,
      default: ''
    },
    isStaff: {
      type: Boolean,
      default: false
    },
    staffSession: {
      type: Boolean,
      default: false
    },
    csrfToken: {
      type: String,
      default: ''
    }
  },
  computed: {
    currentPath() {
      return this.$route.path;
    },
    queryString() {
      return new URLSearchParams(this.$route.query).toString();
    }
  },
  head() {
    return {
      title: this.$t('Not found')
    };
  }
}
</script>