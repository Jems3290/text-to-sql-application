document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.querySelector("[data-file-input]");
    const dropZone = document.querySelector("[data-drop-zone]");
    const uploadForm = document.querySelector("[data-upload-form]");

    const showFile = (file) => {
        if (!file || !dropZone) return;
        dropZone.classList.add("has-file");
        const title = dropZone.querySelector("[data-drop-title]");
        const name = dropZone.querySelector("[data-file-name]");
        if (title) title.textContent = "Database selected";
        if (name) name.textContent = file.name;
    };

    fileInput?.addEventListener("change", () => showFile(fileInput.files[0]));
    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone?.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.add("is-dragging");
        });
    });
    ["dragleave", "drop"].forEach((eventName) => {
        dropZone?.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.remove("is-dragging");
        });
    });
    dropZone?.addEventListener("drop", (event) => {
        const file = event.dataTransfer.files[0];
        if (!file || !fileInput) return;
        const transfer = new DataTransfer();
        transfer.items.add(file);
        fileInput.files = transfer.files;
        showFile(file);
    });
    uploadForm?.addEventListener("submit", () => {
        uploadForm.classList.add("is-submitting");
        const button = uploadForm.querySelector("[data-submit-button]");
        if (button) button.disabled = true;
        const label = uploadForm.querySelector(".button-label");
        if (label) label.textContent = "Validating database…";
    });

    const conversation = document.getElementById("conversation");
    const anchor = document.getElementById("scroll-anchor");
    const input = document.querySelector("[data-message-input]");
    const chatForm = document.querySelector("[data-chat-form]");
    const processing = document.getElementById("processing-message");

    const scrollToLatest = (smooth = false) => {
        anchor?.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "end" });
    };
    scrollToLatest(false);

    const resizeInput = () => {
        if (!input) return;
        input.style.height = "auto";
        input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
    };
    input?.addEventListener("input", resizeInput);
    input?.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            chatForm?.requestSubmit();
        }
    });

    chatForm?.addEventListener("submit", (event) => {
        if (!input?.value.trim()) {
            event.preventDefault();
            input?.focus();
            return;
        }
        const button = chatForm.querySelector("[data-send-button]");
        if (button) button.disabled = true;
        if (processing) processing.hidden = false;
        requestAnimationFrame(() => scrollToLatest(true));
    });

    document.querySelectorAll("[data-suggestion]").forEach((button) => {
        button.addEventListener("click", () => {
            if (!input) return;
            input.value = button.dataset.suggestion || "";
            resizeInput();
            input.focus();
        });
    });

    document.querySelectorAll("[data-copy-sql]").forEach((button) => {
        button.addEventListener("click", async () => {
            const code = button.closest(".sql-code-wrap")?.querySelector("code")?.textContent;
            if (!code) return;
            await navigator.clipboard.writeText(code);
            button.textContent = "Copied";
            window.setTimeout(() => { button.textContent = "Copy"; }, 1400);
        });
    });

    document.querySelectorAll("[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (!window.confirm(form.dataset.confirm)) event.preventDefault();
        });
    });
});
