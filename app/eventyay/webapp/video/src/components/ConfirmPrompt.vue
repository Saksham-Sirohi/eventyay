<template lang="pug">
teleport(to="body")
	transition(name="prompt")
		prompt.c-confirm-prompt(v-if="open", role="dialog", aria-modal="true", :aria-label="title", @close="$emit('close')")
			.content
				h2 {{ title }}
				p {{ message }}
				.prompt-actions
					bunt-button.btn-cancel(@click="$emit('close')") {{ cancelLabel }}
					bunt-button.btn-confirm(@click="$emit('confirm')") {{ confirmLabel }}
</template>
<script>
import Prompt from 'components/Prompt'

export default {
	name: 'ConfirmPrompt',
	components: { Prompt },
	props: {
		open: {
			type: Boolean,
			default: false
		},
		title: {
			type: String,
			required: true
		},
		message: {
			type: String,
			required: true
		},
		confirmLabel: {
			type: String,
			required: true
		},
		cancelLabel: {
			type: String,
			required: true
		}
	},
	emits: ['close', 'confirm']
}
</script>
<style lang="stylus">
.c-confirm-prompt
	.content
		padding: 24px
		display: flex
		flex-direction: column
		h2
			margin: 0 0 12px 0
			font-size: 18px
		p
			margin: 0 0 20px 0
			font-size: 14px
			color: $clr-secondary-text-light
		.prompt-actions
			display: flex
			justify-content: flex-end
			gap: 8px
		.btn-cancel
			button-style(style: clear)
		.btn-confirm
			button-style(color: $clr-danger)
</style>
