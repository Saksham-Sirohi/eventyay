<template lang="pug">
.c-room(v-if="room", :class="{'standalone-chat': modules['chat.native'] && room.modules.length === 1, 'sidebar-collapsed': isSidebarCollapsed}")
	.room-feature-disabled(v-if="roomIsDisabled")
		.disabled-card
			i.mdi.mdi-alert-circle-outline(aria-hidden="true")
			h2 {{ $t('Feature No Longer Available') }}
			p.disabled-message {{ roomDisabledReason }}
			router-link.btn-back-dashboard(:to="{name: 'home'}") {{ $t('Back to Dashboard') }}
	.stage(v-else-if="modules['livestream.native'] || modules['livestream.youtube'] || modules['livestream.vimeo']")
		.stage-canvas-container
			.media-canvas-wrapper
				media-source-placeholder
				reactions-overlay(v-if="hasLivestream")
				upcoming-stream-countdown(:room="room")
		.stage-tool-blocker(v-if="activeStageTool !== null", @click="activeStageTool = null")
		.stage-captions-dock(v-if="hasLivestream && ccEnabled")
			.docked-captions-card
				.captions-header
					.header-left
						i.mdi.mdi-closed-caption
						span.title {{ $t('Live Subtitles') }}
					.header-right
						button.btn-cc-close(@click="toggleCc", :title="$t('Hide Captions')")
							i.mdi.mdi-close
				.captions-scroll-area
					LiveCaptions(:ws-url="selectedCcWsUrl", :text-size="captionTextSize", :docked="true")
		.stage-tools(v-if="hasLivestream")
			.stage-tools-left
				.tool-section.captions-section
					button.stage-tool.cc-toggle(:class="{active: ccEnabled}", @click="toggleCc", :title="$t('Toggle Captions')")
						i.mdi(:class="ccEnabled ? 'mdi-closed-caption' : 'mdi-closed-caption-outline'")
						span.cc-label {{ ccEnabled ? $t('Captions On') : $t('Captions Off') }}
					.size-pills(v-if="ccEnabled")
						button.size-pill(:class="{active: captionTextSize === 'auto'}", @click="setCaptionSize('auto')") {{ $t('Auto') }}
						button.size-pill(:class="{active: captionTextSize === 'normal'}", @click="setCaptionSize('normal')") {{ $t('Normal') }}
						button.size-pill(:class="{active: captionTextSize === 'large'}", @click="setCaptionSize('large')") {{ $t('Large') }}
					.lang-wrapper(v-if="ccEnabled && pluginLanguages.length > 0")
						AudioTranslationDropdown(:key="`${room.id}-cc`", :languages="pluginLanguages", :selected-language="selectedCcLanguage", :label="$t('Caption Language')", @languageChanged="handleCcLanguageChange")
				.tool-section.audio-section
					.dropdown-wrapper(v-if="showPluginLanguageDropdown")
						i.mdi.mdi-account-voice
						AudioTranslationDropdown(:key="`${room.id}-plugin`", :languages="pluginLanguages", :selected-language="selectedPluginLanguage", :label="$t('Interpretation')", @languageChanged="handlePluginLanguageChange")
					.static-audio-pill(v-else)
						i.mdi.mdi-volume-high
						span {{ $t('Original Audio') }}
					.interp-volume-box(v-if="hasInterpretationActive")
						button.interp-mute-btn(@click="toggleInterpMute", :title="interpMuted || interpVolume === 0 ? $t('Unmute Interpretation') : $t('Mute Interpretation')")
							i.mdi(:class="interpMuted || interpVolume === 0 ? 'mdi-volume-off' : 'mdi-volume-high'")
						input.interp-volume-slider(type="range", min="0", max="1", step="0.05", :value="interpMuted ? 0 : interpVolume", @input="onInterpVolumeInput", :aria-label="$t('Interpretation Volume')", :style="{'--interp-vol': interpMuted ? 0 : interpVolume}")
						span.vol-pct {{ Math.round((interpMuted ? 0 : interpVolume) * 100) }}%
			.stage-tools-right
				reactions-bar
	.stage(v-else-if="modules['call.janus'] || modules['call.bigbluebutton'] || modules['call.zoom'] || modules['call.jitsi'] || modules['call.loungemesh']")
		.stage-canvas-container
			.media-canvas-wrapper
				media-source-placeholder
	landing-page(v-else-if="modules['page.landing']", :module="modules['page.landing']")
	markdown-page(v-else-if="modules['page.markdown']", :module="modules['page.markdown']")
	chat(v-else-if="room.modules.length === 1 && modules['chat.native']", :room="room", :module="modules['chat.native']", mode="standalone", :key="room.id")
	.room-sidebar(v-if="hasSidebar", :class="[unreadTabsClasses, { collapsed: isSidebarCollapsed }]", role="complementary")
		.sidebar-edge-tab(v-if="isSidebarCollapsed")
			button.expand-btn(@click.stop="toggleSidebar", :title="$t('Expand Sidebar')")
				i.mdi.mdi-arrow-expand-left
			.edge-tab-actions
				button.edge-item-btn(
					v-if="modules['chat.native']",
					:class="{active: activeSidebarTab === 'chat', unread: unreadTabs['chat']}",
					:title="$t('Chat')",
					@click.stop="selectTabAndExpand('chat')"
				)
					i.mdi.mdi-message-text-outline
					span.unread-dot(v-if="unreadTabs['chat']")
				button.edge-item-btn(
					v-if="modules['question']",
					:class="{active: activeSidebarTab === 'questions', unread: unreadTabs['questions']}",
					:title="$t('Questions')",
					@click.stop="selectTabAndExpand('questions')"
				)
					i.mdi.mdi-help-circle-outline
					span.unread-dot(v-if="unreadTabs['questions']")
				button.edge-item-btn(
					v-if="modules['poll']",
					:class="{active: activeSidebarTab === 'polls', unread: unreadTabs['polls']}",
					:title="$t('Polls')",
					@click.stop="selectTabAndExpand('polls')"
				)
					i.mdi.mdi-poll
					span.unread-dot(v-if="unreadTabs['polls']")
		.sidebar-header(v-if="!isSidebarCollapsed")
			.sidebar-tabs(v-if="visibleTabsCount > 1")
				bunt-tabs(:model-value="activeSidebarTab", @update:modelValue="onTabSelect")
					bunt-tab(v-if="modules['chat.native']", id="chat", :header="$t('Chat')")
					bunt-tab(v-if="modules['question']", id="questions", :header="$t('Questions')")
					bunt-tab(v-if="modules['poll']", id="polls", :header="$t('Polls')")
			.single-tab-title(v-else-if="activeSidebarTab") {{ activeTabTitle }}
			button.sidebar-collapse-btn(@click="toggleSidebar", :title="$t('Collapse Sidebar')")
				i.mdi.mdi-arrow-collapse-right
		.sidebar-body(v-show="!isSidebarCollapsed")
			chat(v-if="modules['chat.native']", v-show="activeSidebarTab === 'chat'", :room="room", :module="modules['chat.native']", mode="compact", :key="room.id", @change="changedTabContent('chat')")
			questions(v-if="modules['question']", v-show="activeSidebarTab === 'questions'", :module="modules['question']", @change="changedTabContent('questions')")
			polls(v-if="modules['poll']", v-show="activeSidebarTab === 'polls'", :module="modules['poll']", @change="changedTabContent('polls')")
</template>
<script>
// TODO
// - questions without chat
// - tab activity
import Chat from 'components/Chat'
import LandingPage from 'components/LandingPage'
import MarkdownPage from 'components/MarkdownPage'
import ReactionsBar from 'components/ReactionsBar'
import ReactionsOverlay from 'components/ReactionsOverlay'
import Polls from 'components/Polls'
import Questions from 'components/Questions'
import MediaSourcePlaceholder from 'components/MediaSourcePlaceholder'
import AudioTranslationDropdown from 'components/AudioTranslationDropdown'
import LiveCaptions from 'components/LiveCaptions'
import UpcomingStreamCountdown from 'components/UpcomingStreamCountdown'
import { normalizeAudioTranslationSource } from 'lib/validators'
import { pluginLanguageStreams, roomUsesPluginLanguageStreams } from '../../interpretation-streams'
import { interpretationApiUrl, interpretationAuthHeaders } from 'lib/interpretation-api'
import { hasOrganizerTraits } from 'lib/traitGrants'
import { hasEmbeddedSuite, isRoomVisibleToAttendee } from 'lib/video-providers'

export default {
	name: 'Room',
	components: {
		Chat,
		LandingPage,
		MarkdownPage,
		ReactionsBar,
		ReactionsOverlay,
		Polls,
		Questions,
		MediaSourcePlaceholder,
		AudioTranslationDropdown,
		LiveCaptions,
		UpcomingStreamCountdown,
	},
	props: {
		room: Object,
		modules: Object
	},
	data() {
		return {
			localActiveSidebarTab: null,
			unreadTabs: {
				chat: false,
				questions: false,
				polls: false
			},
			activeStageTool: null, // reaction, qa
			pluginLanguages: [],
			ccEnabled: false,
			isManualCCOverride: false,
			selectedCcLanguage: 'Original',
			listenerToken: null,
			activeTranslationConfig: null,
			interpMuted: false,
			prevInterpVolume: 0.8,
		}
	},
	computed: {
		activeSidebarTab: {
			get() {
				return this.$store.state.activeRoomSidebarTab || this.localActiveSidebarTab || (this.modules['chat.native'] ? 'chat' : this.modules.question ? 'questions' : this.modules.poll ? 'polls' : null)
			},
			set(tab) {
				this.localActiveSidebarTab = tab
				this.$store.commit('setActiveRoomSidebarTab', tab)
			}
		},
		rooms() {
			return this.$store.state.rooms
		},
		roomIsDisabled() {
			if (!this.room) return false
			if (this.room.is_disabled) return true
			if (this.hasOrganiserPermissions) return false
			return !isRoomVisibleToAttendee(this.room, this.$store.state.world?.video_providers)
		},
		roomDisabledReason() {
			return this.room?.disabled_reason || this.$t('This feature is no longer available. Please contact system administrator.')
		},
		hasOrganiserPermissions() {
			if (!window.eventyay?.isOrganizerArea) return false
			if (window.eventyay?.hasOrganiserPermissions) return true
			const tokenTraits = this.$store.state.user?.traits || []
			return (
				hasOrganizerTraits(tokenTraits) ||
				this.hasPermission('world:users.list') ||
				this.hasPermission('world:update') ||
				this.hasPermission('room:update')
			)
		},
		hasEmbeddedCallSuite() {
			return hasEmbeddedSuite(this.modules)
		},
		canHaveSidebar() {
			if (this.roomIsDisabled) return false
			// Video conference suites (BigBlueButton, Jitsi, Zoom) have their own native in-frame
			// options for chats, polls, questions, etc.; do not show platform native sidebar for them.
			// Janus WebRTC uses native platform chat and displays the sidebar when chat.native is attached.
			if (this.hasEmbeddedCallSuite) return false
			if (this.room?.modules?.length === 1 && this.modules['chat.native']) return false
			return Boolean(
				this.modules['chat.native'] ||
				this.modules['question'] ||
				this.modules['poll']
			)
		},
		hasSidebar() {
			return this.canHaveSidebar
		},
		isSidebarCollapsed() {
			if (!this.room?.id || !this.canHaveSidebar) return false
			const stateVal = this.$store.state.roomSidebarCollapsedByRoom?.[this.room.id]
			return stateVal !== undefined ? Boolean(stateVal) : true
		},
		visibleTabsCount() {
			return (!!this.modules?.['chat.native'] + !!this.modules?.['question'] + !!this.modules?.['poll'])
		},
		availableSidebarTabs() {
			const tabs = []
			if (this.modules?.['chat.native']) tabs.push({ id: 'chat', label: this.$t('Chat') })
			if (this.modules?.['question']) tabs.push({ id: 'questions', label: this.$t('Questions') })
			if (this.modules?.['poll']) tabs.push({ id: 'polls', label: this.$t('Polls') })
			return tabs
		},
		sidebarSummaryText() {
			const labels = this.availableSidebarTabs.map(t => t.label)
			return labels.length > 0 ? labels.join(' • ') : this.$t('Sidebar')
		},
		sidebarSummaryTooltip() {
			return `${this.$t('Expand Sidebar')} (${this.sidebarSummaryText})`
		},
		activeTabTitle() {
			if (this.activeSidebarTab === 'chat') return this.$t('Chat')
			if (this.activeSidebarTab === 'questions') return this.$t('Questions')
			if (this.activeSidebarTab === 'polls') return this.$t('Polls')
			return this.$t('Sidebar')
		},
		hasAnyUnread() {
			return Object.values(this.unreadTabs).some(Boolean)
		},
		interpVolume() {
			return this.$store.state.interpretationVolume ?? 1.0
		},
		captionTextSize() {
			return this.$store.state.captionTextSize || 'auto'
		},
		hasInterpretationActive() {
			return Boolean(this.currentInterpretation?.url || (this.selectedPluginLanguage && this.selectedPluginLanguage !== 'Original'))
		},
		currentInterpretation() {
			if (!this.room?.id) return null
			return this.$store.state.interpretationStreamsByRoom?.[this.room.id] || this.$store.state.youtubeTranslationsByRoom?.[this.room.id] || null
		},
		showPluginLanguageDropdown() {
			return this.pluginLanguages.length > 0
		},
		selectedPluginLanguage() {
			return this.getLanguageForTranslation(this.currentInterpretation, this.pluginLanguages) || 'Original'
		},
		selectedCcWsUrl() {
			if (!this.ccEnabled) return null
			const lang = this.pluginLanguages.find(l => l.language === this.selectedCcLanguage)
			if (lang && lang.caption_ws_url && this.listenerToken) {
				return `${lang.caption_ws_url}${lang.caption_ws_url.includes('?') ? '&' : '?'}token=${this.listenerToken}`
			}
			return null
		},
		usesStreamPolling() {
			return Boolean(
				this.modules['livestream.native'] ||
				this.modules['livestream.youtube'] ||
				this.modules['livestream.vimeo']
			)
		},
		unreadTabsClasses() {
			return Object.entries(this.unreadTabs).filter(([tab, value]) => value).map(([tab]) => `tab-${tab}-unread`)
		},
		hasLivestream() {
			return Boolean(
				this.modules['livestream.native'] ||
				this.modules['livestream.youtube'] ||
				this.modules['livestream.vimeo']
			)
		},

	},
	watch: {
		activeSidebarTab(tab) {
			this.unreadTabs[tab] = false
		},
		room: {
			handler(room, oldRoom) {
				if (room?.id !== oldRoom?.id) {
					this.$store.dispatch('stopStreamPolling')
					this.listenerToken = null
					if (room?.id && this.usesStreamPolling) {
						this.$store.dispatch('startStreamPolling', room.id)
					}
					if (room?.id && this.showPluginLanguageDropdown) {
						this.fetchListenerToken()
					}
				}
				this.initializeLanguages()
				this.checkDirectAccess()
			},
			immediate: true
		},
		rooms: {
			handler() {
				this.checkDirectAccess()
			},
			immediate: true
		},
		'room.currentStream': {
			handler: 'initializeLanguages'
		},
		'room.interpretation_language_streams': {
			handler: 'initializeLanguages'
		},
		'room.interpretation_use_plugin_streams': {
			handler: 'initializeLanguages'
		},
		showPluginLanguageDropdown: {
			handler(val) {
				if (val && this.room?.id && !this.listenerToken) {
					this.fetchListenerToken()
				}
			},
			immediate: true
		}
	},
	async created() {
		if (this.modules['chat.native']) {
			this.activeSidebarTab = 'chat'
		} else if (this.modules.question) {
			this.activeSidebarTab = 'questions'
		} else if (this.modules.poll) {
			this.activeSidebarTab = 'polls'
		}
		if (this.room?.id && this.usesStreamPolling) {
			await this.$nextTick()
			this.$store.dispatch('startStreamPolling', this.room.id)
		}
	},
	mounted() {
		this.checkDirectAccess()
	},
	beforeUnmount() {
		this.$store.dispatch('stopStreamPolling')
	},
	methods: {
		async fetchListenerToken() {
			if (!this.room?.id) return;
			const currentRoomId = this.room.id;
			// Use interpretationApiUrl + interpretationAuthHeaders so X-CSRFToken is included
			const url = interpretationApiUrl(this.$store, this.room.id, 'listener-token/');
			const headers = await interpretationAuthHeaders(true);
			try {
				const response = await fetch(url, { method: 'POST', headers, credentials: 'include' });
				if (this.room?.id !== currentRoomId) return;
				if (response.ok) {
					const data = await response.json();
					if (data && data.token) {
						this.listenerToken = data.token;
					}
				} else {
					console.error('listener-token failed:', response.status);
				}
			} catch (err) {
				if (this.room?.id === currentRoomId) {
					console.error('Failed to fetch listener token', err);
				}
			}
		},
		checkDirectAccess() {
			if (!this.rooms) return
			if (!this.hasOrganiserPermissions) {
				const roomId = this.roomId || this.$route.params.roomId
				if (roomId && (!this.room || this.roomIsDisabled)) {
					this.$router.replace({ name: 'about' })
				}
			}
		},
		changedTabContent(tab) {
			const isViewingTab = !this.isSidebarCollapsed && tab === this.activeSidebarTab
			if (isViewingTab) return
			this.unreadTabs[tab] = true
		},
		handlePluginLanguageChange(translationConfig) {
			this.updateActiveTranslation(translationConfig)
			if (!this.isManualCCOverride && this.ccEnabled) {
				this.selectedCcLanguage = this.getLanguageForTranslation(translationConfig, this.pluginLanguages) || 'Original'
			}
		},
		handleCcLanguageChange(translationConfig) {
			this.isManualCCOverride = true
			this.selectedCcLanguage = this.getLanguageForTranslation(translationConfig, this.pluginLanguages) || 'Original'
		},
		toggleCc() {
			this.ccEnabled = !this.ccEnabled
			if (this.ccEnabled && !this.isManualCCOverride) {
				this.selectedCcLanguage = this.selectedPluginLanguage
			}
		},
		updateActiveTranslation(translationConfig) {
			this.activeTranslationConfig = translationConfig;
			this.recomputeInterpretationAudio();
		},
		recomputeInterpretationAudio() {
			let finalConfig = this.activeTranslationConfig;
			if (finalConfig && finalConfig.language === 'Original') {
				finalConfig = null;
			}
			if (finalConfig && !finalConfig.url && !finalConfig.youtube_id) {
				finalConfig = null;
			}
			this.$store.commit('updateInterpretationAudio', {
				roomId: this.room?.id,
				interpretation: finalConfig
			})
		},
		initializeLanguages() {
			this.pluginLanguages = roomUsesPluginLanguageStreams(this.room)
				? pluginLanguageStreams(this.room)
				: [{ language: 'Original', url: null, youtube_id: null, use_video: false }]
			this.clearStaleTranslation()
		},
		getLanguageForTranslation(translationConfig, languages) {
			if (!translationConfig?.url || !languages?.length) return 'Original'
			const matchingLanguage = languages.find(entry => (
				entry.language !== 'Original' &&
				normalizeAudioTranslationSource(entry.url || entry.youtube_id) === translationConfig.url &&
				!!entry.use_video === !!translationConfig.useVideo
			))
			return matchingLanguage?.language || null
		},
		clearStaleTranslation() {
			if (!this.room?.id || !this.currentInterpretation) return
			const matchesPlugin = this.getLanguageForTranslation(this.currentInterpretation, this.pluginLanguages)
			if (!this.showPluginLanguageDropdown || !matchesPlugin) {
				this.$store.commit('updateInterpretationAudio', {
					roomId: this.room.id,
					interpretation: null
				})
			}
		},
		toggleSidebar() {
			if (!this.room?.id) return
			const nextState = !this.isSidebarCollapsed
			this.$store.commit('setRoomSidebarCollapsed', {
				roomId: this.room.id,
				collapsed: nextState
			})
			if (!nextState && this.activeSidebarTab) {
				this.unreadTabs[this.activeSidebarTab] = false
			}
			this.$nextTick(() => {
				window.dispatchEvent(new Event('resize'))
			})
		},
		selectTabAndExpand(tab) {
			this.activeSidebarTab = tab
			this.unreadTabs[tab] = false
			if (this.isSidebarCollapsed) {
				this.toggleSidebar()
			}
		},
		onTabSelect(tab) {
			if (!tab) return
			this.activeSidebarTab = tab
		},
		toggleInterpMute() {
			if (this.interpMuted || this.interpVolume === 0) {
				this.interpMuted = false
				this.$store.commit('setInterpretationVolume', this.prevInterpVolume || 0.8)
			} else {
				this.prevInterpVolume = this.interpVolume || 0.8
				this.interpMuted = true
				this.$store.commit('setInterpretationVolume', 0)
			}
		},
		onInterpVolumeInput(event) {
			const val = parseFloat(event.target.value)
			this.interpMuted = val === 0
			this.$store.commit('setInterpretationVolume', val)
		},
		cycleCaptionSize() {
			const order = ['auto', 'normal', 'large']
			const next = order[(order.indexOf(this.captionTextSize) + 1) % order.length]
			this.$store.commit('setCaptionTextSize', next)
		},
		setCaptionSize(size) {
			this.$store.commit('setCaptionTextSize', size)
		}
	}
}
</script>
<style lang="stylus">
.c-room
	flex: auto
	height: 100%
	display: flex
	min-height: 0
	min-width: 0
	max-width: 100%
	overflow: hidden
	position: relative

	.stage
		display: flex
		flex-direction: column
		height: 100%
		min-height: 0
		min-width: 0
		max-width: 100%
		flex: 1 1 0
		width: 0
		overflow: hidden
		position: relative
		background-color: var(--clr-grey-50, #f8f9fa)

		+below('m')
			height: auto
			overflow-y: auto

		.stage-canvas-container
			flex: 1 1 0
			min-height: 0
			min-width: 0
			display: flex
			align-items: flex-start
			justify-content: center
			position: relative
			width: 100%
			overflow: hidden
			padding: 0
			box-sizing: border-box
			container-type: size

			.media-canvas-wrapper
				position: relative
				aspect-ratio: 16 / 9
				width: unquote('min(100cqw, calc(100cqh * 16 / 9))')
				max-width: 100%
				max-height: 100%
				display: flex
				align-items: center
				justify-content: center
				border-radius: 4px
				overflow: hidden
				border: none
				box-shadow: none
				background-color: transparent

				.c-media-source-placeholder
					position: absolute
					top: 0
					left: 0
					width: 100%
					height: 100%
					min-height: 0
					min-width: 0

		.stage-tools
			flex: none
			min-height: 0
			height: auto
			display: flex
			align-items: center
			justify-content: space-between
			width: 100%
			box-sizing: border-box
			padding: 6px 12px
			background-color: var(--clr-surface, #ffffff)
			border-top: 1px solid var(--clr-grey-200, #e2e8f0)
			border-bottom: 1px solid var(--clr-grey-200, #e2e8f0)
			user-select: none
			color: var(--clr-text-primary, #1e293b)
			z-index: 10
			gap: 12px

			.stage-tools-left
				display: flex
				flex-direction: column
				align-items: flex-start
				justify-content: center
				gap: 4px
				min-width: 0
				flex: 1 1 auto

				.tool-section
					display: inline-flex
					align-items: center
					gap: 6px
					flex-wrap: wrap
					padding: 3px 5px
					border: 1px solid var(--clr-grey-200, #e2e8f0)
					border-radius: 6px
					background: var(--clr-grey-50, #f8f9fa)
					width: fit-content

				.static-audio-pill
					display: inline-flex
					align-items: center
					gap: 4px
					height: 26px
					padding: 0 8px
					border-radius: 13px
					background: var(--clr-grey-100, #f1f5f9)
					color: var(--clr-text-secondary, #64748b)
					font-size: 11px
					font-weight: 500
					.mdi
						font-size: 14px
						color: var(--clr-primary, #2185d0)

				.interp-volume-box
					display: inline-flex
					align-items: center
					gap: 4px
					height: 26px
					padding: 0 6px
					border-radius: 6px
					background: var(--clr-grey-100, #f1f5f9)
					.interp-mute-btn
						display: flex
						align-items: center
						justify-content: center
						width: 20px
						height: 20px
						border: none
						background: transparent
						color: var(--clr-text-primary, #1e293b)
						cursor: pointer
						padding: 0
						.mdi
							font-size: 14px
					.interp-volume-slider
						width: 56px
						height: 3px
						accent-color: var(--clr-primary, #2185d0)
						cursor: pointer
					.vol-pct
						font-size: 11px
						font-weight: 600
						color: var(--clr-text-secondary, #64748b)
						min-width: 28px

				.dropdown-wrapper
					display: flex
					align-items: center
					gap: 4px
					color: var(--clr-text-secondary, #64748b)
					.mdi
						font-size: 16px
						color: var(--clr-primary, #2185d0)

				.stage-tool.cc-toggle
					display: inline-flex
					align-items: center
					gap: 4px
					height: 26px
					padding: 0 8px
					border-radius: 5px
					border: 1px solid var(--clr-grey-300, #cbd5e1)
					background: var(--clr-surface, #ffffff)
					color: var(--clr-text-secondary, #64748b)
					font-size: 11px
					font-weight: 500
					cursor: pointer
					transition: all 0.15s ease
					&:hover
						border-color: var(--clr-primary, #2185d0)
						color: var(--clr-primary, #2185d0)
					&.active
						background-color: var(--clr-primary-alpha-18, rgba(33, 133, 208, 0.12))
						border-color: var(--clr-primary, #2185d0)
						color: var(--clr-primary, #2185d0)
						font-weight: 600
					.mdi
						font-size: 15px

				.size-pills
					display: inline-flex
					border: 1px solid var(--clr-grey-300, #cbd5e1)
					border-radius: 5px
					overflow: hidden
					height: 26px

					.size-pill
						border: none
						background: var(--clr-surface, #ffffff)
						padding: 0 8px
						font-size: 11px
						font-weight: 500
						color: var(--clr-text-secondary, #64748b)
						cursor: pointer
						transition: all 0.15s ease
						border-right: 1px solid var(--clr-grey-200, #e2e8f0)
						&:last-child
							border-right: none
						&:hover
							background-color: var(--clr-grey-100, #f1f5f9)
							color: var(--clr-primary, #2185d0)
						&.active
							background-color: var(--clr-primary, #2185d0)
							color: #ffffff
							font-weight: 600

			.stage-tools-right
				display: flex
				align-items: center
				gap: 8px
				flex: none

		.stage-captions-dock
			flex: none
			height: 110px
			display: flex
			flex-direction: column
			padding: 4px 16px 8px
			box-sizing: border-box
			overflow: hidden

			.docked-captions-card
				flex: 1
				min-height: 0
				display: flex
				flex-direction: column
				background: var(--clr-surface, #ffffff)
				border: 1px solid var(--clr-grey-200, #e2e8f0)
				border-radius: 6px
				overflow: hidden
				box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04)

				.captions-header
					display: flex
					align-items: center
					justify-content: space-between
					height: 28px
					padding: 0 10px
					background-color: var(--clr-grey-100, #f1f5f9)
					border-bottom: 1px solid var(--clr-grey-200, #e2e8f0)
					flex: none

					.header-left
						display: flex
						align-items: center
						gap: 6px
						font-size: 11px
						font-weight: 600
						color: var(--clr-text-primary, #1e293b)
						.mdi
							font-size: 15px
							color: var(--clr-primary, #2185d0)

					.header-right
						.btn-cc-close
							display: flex
							align-items: center
							justify-content: center
							width: 20px
							height: 20px
							border: none
							background: transparent
							color: var(--clr-text-secondary, #64748b)
							cursor: pointer
							border-radius: 3px
							&:hover
								background: var(--clr-grey-200, #e2e8f0)
								color: var(--clr-text-primary, #1e293b)
							.mdi
								font-size: 14px

				.captions-scroll-area
					flex: 1
					min-height: 0
					overflow: hidden
					padding: 2px 10px
					display: flex
					flex-direction: column

	.room-sidebar
		display: flex
		flex-direction: column
		min-height: 0
		flex: none
		width: var(--chatbar-width, 285px)
		border-left: border-separator()
		background-color: var(--clr-surface, #ffffff)
		overflow: hidden

		&.collapsed
			width: 44px

			.sidebar-edge-tab
				display: flex
				flex-direction: column
				align-items: center
				justify-content: flex-start
				height: 100%
				width: 44px
				padding: 8px 0
				box-sizing: border-box
				user-select: none
				background-color: var(--clr-surface, #ffffff)

				.expand-btn
					display: flex
					align-items: center
					justify-content: center
					width: 32px
					height: 32px
					border-radius: 4px
					border: none
					background: transparent
					color: var(--clr-text-secondary, #757575)
					cursor: pointer
					margin-bottom: 8px
					transition: all 0.15s ease
					&:hover
						background: var(--clr-grey-100, #f5f5f5)
						color: var(--clr-primary, #2185d0)
					.mdi
						font-size: 20px

				.edge-tab-actions
					display: flex
					flex-direction: column
					align-items: center
					gap: 6px
					width: 100%

					.edge-item-btn
						position: relative
						display: flex
						align-items: center
						justify-content: center
						width: 32px
						height: 32px
						border-radius: 4px
						border: 1px solid transparent
						background: transparent
						color: var(--clr-text-secondary, #757575)
						cursor: pointer
						transition: all 0.15s ease
						&:hover
							background-color: var(--clr-grey-100, #f5f5f5)
							color: var(--clr-primary, #2185d0)
						&.active
							color: var(--clr-primary, #2185d0)
							background-color: var(--clr-primary-alpha-18, rgba(33, 133, 208, 0.12))
							border-color: var(--clr-primary, #2185d0)
						.mdi
							font-size: 20px

						.unread-dot
							position: absolute
							top: 2px
							right: 2px
							width: 7px
							height: 7px
							border-radius: 50%
							background-color: $clr-danger
							animation: pulse 2s infinite

		.sidebar-header
			display: flex
			align-items: center
			justify-content: space-between
			height: 48px
			border-bottom: border-separator()
			background-color: var(--clr-surface, #ffffff)
			padding: 0 4px 0 8px
			box-sizing: border-box
			flex: none

			.sidebar-tabs
				flex: 1
				min-width: 0
				height: 100%
				overflow: hidden

				.bunt-tabs
					tabs-style(active-color: var(--clr-primary, #2185d0), indicator-color: var(--clr-primary, #2185d0), background-color: transparent)
					width: 100%
					margin: 0
					height: 100%

				.bunt-tabs-header
					height: 100%
					background: transparent

				.bunt-tabs-header-items
					height: 100%
					justify-content: flex-start

				.bunt-tabs-body
					display: none

				.bunt-tab-header-item
					height: 48px
					min-width: 64px
					padding: 0 10px
					font-size: 13px
					font-weight: 600
					text-transform: uppercase

			.single-tab-title
				font-size: 15px
				font-weight: 600
				color: var(--clr-text-primary, #212121)
				padding-left: 8px
				flex: 1

			.sidebar-collapse-btn
				flex: none
				display: flex
				align-items: center
				justify-content: center
				width: 32px
				height: 32px
				border-radius: 4px
				border: none
				background: transparent
				color: var(--clr-text-secondary, #757575)
				cursor: pointer
				transition: all 0.15s ease
				&:hover
					background: var(--clr-grey-100, #f5f5f5)
					color: var(--clr-primary, #2185d0)
				.mdi
					font-size: 20px

		.sidebar-body
			flex: 1 1 0
			min-height: 0
			min-width: 0
			display: flex
			flex-direction: column
			overflow: hidden

			> .c-chat,
			> .c-questions,
			> .c-polls
				flex: 1 1 0
				min-height: 0
				min-width: 0
				width: 100%

		for tab in chat questions polls
			&.tab-{tab}-unread [aria-controls="{tab}"] .bunt-tab-header-item-text
				position: relative
				&::after
					content: ''
					position: absolute
					top: -2px
					right: -8px
					display: block
					height: 6px
					width: 6px
					border-radius: 50%
					background-color: $clr-danger

	.stage-tool-blocker
		position: fixed
		top: 0
		left: 0
		width: 100vw
		height: var(--vh100)
		z-index: 800

	&.standalone-chat
		flex: auto
	&:not(.standalone-chat)
		.c-chat
			min-height: 0
			flex-direction: column

	+below('m')
		flex-direction: column
		.stage
			flex: none
			width: 100%
			.stage-canvas-container
				height: var(--mobile-media-height, 56.25vw)
				flex: none
				.media-canvas-wrapper
					width: 100%
					height: 100%
					max-width: 100%
					border-radius: 4px
		.room-sidebar
			flex: auto
			width: 100%
			min-height: 0
			&.collapsed
				flex: none
				height: 44px
				width: 100%
				border-left: none
				border-top: border-separator()

				.sidebar-edge-tab
					flex-direction: row
					justify-content: flex-start
					align-items: center
					width: 100%
					height: 44px
					padding: 0 8px
					gap: 8px

					.expand-btn
						margin-bottom: 0

					.edge-tab-actions
						flex-direction: row
						gap: 12px
						width: auto
		&:not(.standalone-chat)
			.c-chat
				flex: auto
				width: 100%
				min-height: 0

	.room-feature-disabled
		display: flex
		flex-direction: column
		align-items: center
		justify-content: center
		width: 100%
		height: 100%
		min-height: 60vh
		padding: 32px
		background-color: $clr-grey-50
		flex: auto

		.disabled-card
			max-width: 520px
			text-align: center
			padding: 40px 32px
			background-color: $clr-white
			border: 1px solid $clr-grey-200
			border-radius: 8px
			box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05)

			i.mdi
				font-size: 56px
				color: #d9534f
				margin-bottom: 16px
				display: block

			h2
				font-size: 22px
				font-weight: 600
				color: $clr-grey-900
				margin: 0 0 12px

			.disabled-message
				font-size: 15px
				line-height: 1.5
				color: $clr-grey-700
				margin: 0 0 24px

			.btn-back-dashboard
				display: inline-block
				padding: 9px 22px
				background-color: #337ab7
				color: #ffffff
				border-radius: 4px
				font-size: 14px
				font-weight: 500
				text-decoration: none
				transition: background-color 0.15s ease
				&:hover
					background-color: #286090
					text-decoration: none

@keyframes pulse
	0%
		transform: scale(0.95)
		box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7)
	70%
		transform: scale(1)
		box-shadow: 0 0 0 6px rgba(239, 68, 68, 0)
	100%
		transform: scale(0.95)
		box-shadow: 0 0 0 0 rgba(239, 68, 68, 0)
</style>
