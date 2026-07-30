const submissionVideoDialog = (() => {
    let controller = null

    return () => {
        if (controller) return controller

        const dialog = document.getElementById('submission-video-dialog')
        const form = document.getElementById('submission-video-form')
        const input = document.getElementById('submission-video-url-input')
        const errorEl = document.getElementById('submission-video-error')
        const titleEl = document.getElementById('submission-video-session-title')
        const clearBtn = document.getElementById('submission-video-clear')
        if (!dialog || !form || !input) return null

        let activeButton = null
        let saveUrl = ''

        const showError = (message) => {
            if (!errorEl) return
            errorEl.textContent = message || ''
            errorEl.classList.toggle('d-none', !message)
        }

        const setButtonState = (button, hasVideo, videoUrl) => {
            if (!button) return
            button.dataset.videoUrl = videoUrl || ''
            button.classList.toggle('btn-success', !!hasVideo)
            button.classList.toggle('btn-outline-secondary', !hasVideo)
            const label = hasVideo
                ? (button.dataset.editLabel || 'Edit video link')
                : (button.dataset.addLabel || 'Add video link')
            button.title = label
            button.setAttribute('aria-label', label)
        }

        const openForButton = (button) => {
            activeButton = button
            saveUrl = button.dataset.url || ''
            if (titleEl) {
                titleEl.textContent = button.dataset.title || ''
            }
            input.value = button.dataset.videoUrl || ''
            showError('')
            if (typeof dialog.showModal === 'function' && !dialog.open) {
                dialog.showModal()
                input.focus()
                input.select()
            }
        }

        const save = async (urlValue) => {
            if (!saveUrl) return
            showError('')
            try {
                const response = await fetch(saveUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('eventyay_csrftoken'),
                    },
                    credentials: 'include',
                    body: JSON.stringify({ url: urlValue }),
                })
                let data = {}
                try {
                    data = await response.json()
                } catch (parseError) {
                    console.error('Failed to parse video link response', parseError)
                }
                if (!response.ok || !data.ok) {
                    showError(data.error || 'Could not save video link.')
                    return false
                }
                setButtonState(activeButton, data.has_video, data.url || '')
                if (typeof dialog.close === 'function') {
                    dialog.close()
                }
                return true
            } catch (error) {
                console.error('Failed to save session video link', error)
                showError('Could not save video link.')
                return false
            }
        }

        form.addEventListener('submit', (event) => {
            const submitter = event.submitter
            if (submitter && submitter.value === 'cancel') {
                return
            }
            event.preventDefault()
            save(input.value.trim())
        })

        if (clearBtn) {
            clearBtn.addEventListener('click', (event) => {
                event.preventDefault()
                input.value = ''
                save('')
            })
        }

        dialog.addEventListener('click', (event) => {
            if (event.target === dialog && typeof dialog.close === 'function') {
                dialog.close()
            }
        })

        controller = { openForButton }
        return controller
    }
})()

const initSubmissionVideoButtons = (root = document) => {
    const controller = submissionVideoDialog()
    if (!controller) return

    root.querySelectorAll('.submission-video-btn:not([data-video-initialized])').forEach((button) => {
        button.setAttribute('data-video-initialized', '')
        button.addEventListener('click', () => {
            controller.openForButton(button)
        })
    })
}

onReady(() => {
    initSubmissionVideoButtons()
})

document.addEventListener('eventyay:ajax-results-replaced', (event) => {
    initSubmissionVideoButtons(event.detail?.container ?? document)
})
