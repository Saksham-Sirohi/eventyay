document
    .querySelector("button#generate-widget")
    ?.addEventListener("click", () => {
        document.querySelector("#widget-generation")?.classList.add("d-none")
        document.querySelector("#generated-widget")?.classList.remove("d-none")
        const secondPre = document.querySelector("pre#widget-body")
        const localeEl = document.querySelector("#id_locale")
        const daysEl = document.querySelector("#id_days")
        if (!secondPre || !localeEl) return

        const locale = localeEl.value
        secondPre.innerHTML = secondPre.innerHTML.replace("LOCALE", locale)

        const days = daysEl
            ? Array.from(daysEl.querySelectorAll("option:checked"), (option) => option.value)
            : []
        if (days.length) {
            secondPre.innerHTML = secondPre.innerHTML.replace(
                "FILTER_DAYS",
                ` date-filter="${days.join(",")}"`
            )
        } else {
            secondPre.innerHTML = secondPre.innerHTML.replace("FILTER_DAYS", "")
        }

        const previewMount = document.querySelector("#widget-preview-mount")
        if (!previewMount) return

        previewMount.replaceChildren()
        const schedule = document.createElement("pretalx-schedule")
        schedule.setAttribute("event-url", previewMount.dataset.eventUrl)
        schedule.setAttribute("locale", locale)
        schedule.style.setProperty(
            "--pretalx-clr-primary",
            previewMount.dataset.primaryColor || "#2185d0"
        )
        if (days.length) {
            schedule.setAttribute("date-filter", days.join(","))
        }
        previewMount.appendChild(schedule)
    })
