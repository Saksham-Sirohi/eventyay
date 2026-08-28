<template lang="pug">
.v-presentation-question(:class="[mode, { 'empty-question': !displayQuestion }]")
	.question-stage-header(v-if="showStageHeader")
		.live-indicator
			span.pulse-dot
		h2.room-name(v-if="room", v-html="$emojify(room.name)")
	template(v-if="displayQuestion")
		.question {{ displayQuestion.content }}
		.info
			.votes
				.mdi.mdi-thumb-up
				.vote-count {{ displayQuestion.score }}
			.user(v-if="sender")
				avatar(:user="sender", :size="mode === 'compact' ? 32 : 48")
				.username {{ senderDisplayName }}
	.empty-card(v-else)
		i.mdi.mdi-comment-question-outline
		h2 {{ $t('No Pinned Question') }}
		p {{ emptyHint }}
</template>
<script>
import { mapState, mapGetters } from 'vuex'
import Avatar from 'components/Avatar'

export default {
	components: { Avatar },
	props: {
		room: Object,
		mode: {
			type: String,
			default: 'focus'
		}
	},
	computed: {
		...mapState('chat', ['usersLookup']),
		...mapState('question', ['questions']),
		...mapGetters('question', ['pinnedQuestion']),
		topVisibleQuestion() {
			if (!this.questions) return null
			const visible = this.questions
				.filter(question => question.state === 'visible')
				.slice()
				.sort((a, b) => (b.score || 0) - (a.score || 0))
			return visible[0] || null
		},
		displayQuestion() {
			return this.pinnedQuestion || this.topVisibleQuestion
		},
		showStageHeader() {
			return false
		},
		emptyHint() {
			if (this.mode === 'compact') {
				return this.$t('Approve questions in Manage to list them here. Pin one to show it full screen.')
			}
			return this.$t('Pinned audience questions will appear here during the session.')
		},
		sender() {
			if (!this.displayQuestion) return null
			return this.usersLookup[this.displayQuestion.sender]
		},
		senderDisplayName() {
			return this.sender?.profile?.display_name ?? this.displayQuestion?.sender
		},
	},
	watch: {
		displayQuestion: {
			handler(question) {
				if (question?.sender) this.fetchSender()
			},
			immediate: true
		}
	},
	methods: {
		fetchSender() {
			if (!this.displayQuestion?.sender) return
			this.$store.dispatch('chat/fetchUsers', [this.displayQuestion.sender])
		}
	}
}
</script>
<style lang="stylus">
.v-presentation-question
	display: flex
	flex-direction: column
	justify-content: flex-start
	width: 100%
	max-width: none
	height: 100%
	margin: 0
	padding: 20px 24px
	box-sizing: border-box
	background: #ffffff
	color: #1e2327
	overflow: auto

	&.compact
		max-width: none
		padding: 4px
		.question
			font-size: 16px
		.info
			margin-top: 12px
			padding-top: 8px
			.votes .mdi, .votes .vote-count
				font-size: 18px
		.empty-card
			i.mdi
				font-size: 36px
				margin-bottom: 8px
			h2
				font-size: 16px
			p
				font-size: 12px

	.question-stage-header
		display: none

	.question
		font-size: 32px
		font-weight: 700
		line-height: 1.35
		color: #1e2327
	.info
		display: flex
		justify-content: space-between
		align-items: center
		align-self: stretch
		padding: 12px 0 0
		margin-top: 20px
		border-top: 1px solid #e5e7eb
		.votes
			display: flex
			align-items: center
			.mdi
				font-size: 24px
				color: var(--clr-primary, #2185d0)
			.vote-count
				margin: 0 0 0 8px
				font-size: 24px
				font-weight: 700
				color: #1e2327
		.user
			display: flex
			align-items: center
			.username
				margin: 0 0 0 8px
				color: #4b5563
				font-weight: 600

	.empty-card
		display: flex
		flex-direction: column
		align-items: center
		justify-content: center
		text-align: center
		flex: 1
		color: #4b5563
		i.mdi
			font-size: 56px
			margin-bottom: 16px
			color: var(--clr-primary, #2185d0)
		h2
			margin: 0 0 8px
			font-size: 22px
			font-weight: 700
			color: #1e2327
		p
			margin: 0
			max-width: 400px
			font-size: 15px
</style>
