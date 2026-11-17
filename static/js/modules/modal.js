// ==========================================================================
// Módulo: modal.js
// Cabeça de Droid - Vanilla ES6 Module
// ==========================================================================

// ==========================================================================
// MODAL DE PIN & FEEDBACK VISUAL (TOASTS)
// ==========================================================================
function showPinLockModal() {
    const modal = document.getElementById("modal-pin-lock");
    if (modal) {
        modal.style.display = "flex";
        const pinInput = document.getElementById("pin-unlock-input");
        if (pinInput) {
            pinInput.value = "";
            updatePinDots("");
            pinInput.focus();
        }
        const errorEl = document.getElementById("pin-error-msg");
        if (errorEl) errorEl.innerText = "";
    }
}

function hidePinLockModal() {
    const modal = document.getElementById("modal-pin-lock");
    if (modal) {
        modal.style.display = "none";
    }
}

function updatePinDots(val) {
    const dotsBox = document.getElementById("pin-dots-box");
    if (!dotsBox) return;
    const dots = dotsBox.querySelectorAll(".pin-dot");
    dots.forEach((dot, idx) => {
        if (idx < val.length) {
            dot.classList.add("filled");
        } else {
            dot.classList.remove("filled");
        }
    });
}

function setupPinSecurityUI() {
    const pinInput = document.getElementById("pin-unlock-input");
    const submitBtn = document.getElementById("btn-submit-unlock-pin");
    const errorEl = document.getElementById("pin-error-msg");

    if (pinInput) {
        pinInput.addEventListener("input", () => {
            pinInput.value = pinInput.value.replace(/\D/g, "").slice(0, 6);
            updatePinDots(pinInput.value);
            if (errorEl) errorEl.innerText = "";
            if (pinInput.value.length === 6) {
                submitPinUnlock();
            }
        });

        pinInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                submitPinUnlock();
            }
        });
    }

    if (submitBtn) {
        submitBtn.addEventListener("click", submitPinUnlock);
    }

    async function submitPinUnlock() {
        const pin = pinInput ? pinInput.value : "";
        if (!pin || pin.length < 4) {
            if (errorEl) errorEl.innerText = "Digite de 4 a 6 dígitos numéricos.";
            return;
        }

        try {
            if (submitBtn) submitBtn.disabled = true;
            const res = await originalFetch("/api/security/pin/verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ pin })
            });
            const data = await res.json();

            if (res.ok && data.status === "ok") {
                if (submitBtn && typeof submitBtn.done === "function") submitBtn.done();
                hidePinLockModal();
                showToast("Acesso desbloqueado com sucesso!", "success");
                fetchConfig();
                loadOverview();
                loadRoster("zzz");
                loadRoster("genshin");
                loadRoster("hsr");
            } else {
                if (errorEl) errorEl.innerText = data.detail || "PIN incorreto. Tente novamente.";
                if (pinInput) {
                    pinInput.value = "";
                    updatePinDots("");
                    pinInput.focus();
                }
            }
        } catch (err) {
            if (errorEl) errorEl.innerText = "Erro ao conectar com o servidor.";
        } finally {
            if (submitBtn) submitBtn.disabled = false;
        }
    }
}

function showToast(message, type = "info") {
    const sakugaToast = document.getElementById("sakuga-global-toast");
    if (sakugaToast && typeof sakugaToast.show === "function") {
        if (type === "error") {
            sakugaToast.style.setProperty("--sk-pri", "#ef4444");
            sakugaToast.style.setProperty("--sk-ink", "#fecaca");
        } else if (type === "success") {
            sakugaToast.style.setProperty("--sk-pri", "#10b981");
            sakugaToast.style.setProperty("--sk-ink", "#f8fafc");
        } else {
            sakugaToast.style.setProperty("--sk-pri", "#8b5cf6");
            sakugaToast.style.setProperty("--sk-ink", "#f8fafc");
        }
        sakugaToast.show(String(message || ""));
    }
}
window.showToast = showToast;



function showSakugaConfirm(message, title = "Confirmar Ação") {
    const modal = document.getElementById("modal-sakuga-confirm");
    const titleEl = document.getElementById("sakuga-confirm-title");
    const msgEl = document.getElementById("sakuga-confirm-message");
    const btnOk = document.getElementById("btn-sakuga-confirm-ok");
    const btnCancel = document.getElementById("btn-sakuga-confirm-cancel");

    if (!modal || !msgEl || !btnOk || !btnCancel) {
        return Promise.resolve(window.confirm(String(message || "")));
    }

    if (titleEl) titleEl.textContent = title;
    msgEl.textContent = String(message || "");
    modal.style.display = "flex";

    return new Promise((resolve) => {
        const cleanup = (result) => {
            modal.style.display = "none";
            btnOk.removeEventListener("click", onOk);
            btnCancel.removeEventListener("click", onCancel);
            modal.removeEventListener("click", onOverlay);
            document.removeEventListener("keydown", onKey);
            resolve(result);
        };
        const onOk = () => cleanup(true);
        const onCancel = () => cleanup(false);
        const onOverlay = (e) => {
            if (e.target === modal) cleanup(false);
        };
        const onKey = (e) => {
            if (e.key === "Escape") cleanup(false);
            if (e.key === "Enter") cleanup(true);
        };
        btnOk.addEventListener("click", onOk);
        btnCancel.addEventListener("click", onCancel);
        modal.addEventListener("click", onOverlay);
        document.addEventListener("keydown", onKey);
    });
}
window.showSakugaConfirm = showSakugaConfirm;

// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof hidePinLockModal !== 'undefined') window.hidePinLockModal = hidePinLockModal;
if (typeof setupPinSecurityUI !== 'undefined') window.setupPinSecurityUI = setupPinSecurityUI;
if (typeof showPinLockModal !== 'undefined') window.showPinLockModal = showPinLockModal;
if (typeof showToast !== 'undefined') window.showToast = showToast;
if (typeof showSakugaConfirm !== 'undefined') window.showSakugaConfirm = showSakugaConfirm;
if (typeof updatePinDots !== 'undefined') window.updatePinDots = updatePinDots;