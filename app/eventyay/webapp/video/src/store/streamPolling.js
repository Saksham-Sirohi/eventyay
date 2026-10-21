export const STREAM_POLL_BASE_DELAY = 60000
export const STREAM_POLL_MAX_DELAY = 300000
export const STREAM_POLL_MAX_TRANSIENT_ERRORS = 5
export const STREAM_POLL_PERMANENT_STATUSES = [401, 403]

export function httpErrorStatus (error) {
	return error?.status ?? error?.response?.status
}

export function isPermanentStreamPollError (error) {
	return STREAM_POLL_PERMANENT_STATUSES.includes(httpErrorStatus(error))
}

export function nextStreamPollDelay (currentDelay, maxDelay = STREAM_POLL_MAX_DELAY) {
	return Math.min((currentDelay || STREAM_POLL_BASE_DELAY) * 2, maxDelay)
}

export function shouldStopAfterTransientErrors (count) {
	return count >= STREAM_POLL_MAX_TRANSIENT_ERRORS
}

export function streamPollJitter (ms) {
	return ms + Math.random() * 2000
}

export function usesHttpStreamFallback (connected) {
	return !connected
}

export function secondsUntilStart (start, nowMs = Date.now()) {
	const startMs = typeof start === 'number' ? start : Date.parse(start)
	if (!Number.isFinite(startMs)) return null
	const remainingMs = startMs - nowMs
	if (remainingMs <= 0) return 0
	return Math.ceil(remainingMs / 1000)
}

export function streamIsActive (stream, nowMs = Date.now()) {
	if (!stream?.url) return false
	const start = stream.start_time ? Date.parse(stream.start_time) : NaN
	const end = stream.end_time ? Date.parse(stream.end_time) : NaN
	if (Number.isFinite(start) && start > nowMs) return false
	if (Number.isFinite(end) && end <= nowMs) return false
	return true
}

export function earliestFutureMs (timestamps, nowMs = Date.now()) {
	const future = timestamps
		.map((value) => (typeof value === 'number' ? value : Date.parse(value)))
		.filter((value) => Number.isFinite(value) && value > nowMs)
	if (!future.length) return null
	return Math.min(...future)
}
