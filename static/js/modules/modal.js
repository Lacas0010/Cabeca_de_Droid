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
            pinInput.value = pinInput.value.replace(/\D/g, "");
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
    let container = document.getElementById("app-toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "app-toast-container";
        container.style.cssText = "position: fixed; bottom: 24px; right: 24px; z-index: 100000; display: flex; flex-direction: column; gap: 8px; pointer-events: none;";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    const colors = {
        success: "background: rgba(16, 185, 129, 0.95); border: 1px solid #10b981; color: #fff;",
        error: "background: rgba(239, 68, 68, 0.95); border: 1px solid #ef4444; color: #fff;",
        info: "background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(168, 85, 247, 0.5); color: #e2e8f0;"
    };
    const icons = {
        success: '<i class="fa-solid fa-circle-check"></i>',
        error: '<i class="fa-solid fa-circle-exclamation"></i>',
        info: '<i class="fa-solid fa-circle-info" style="color: #a855f7;"></i>'
    };

    toast.style.cssText = `padding: 10px 18px; border-radius: 10px; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); backdrop-filter: blur(8px); transition: all 0.3s ease; opacity: 0; transform: translateY(10px); pointer-events: auto; ${colors[type] || colors.info}`;
    toast.innerHTML = `${icons[type] || icons.info} <span>${message}</span>`;
    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.opacity = "1";
        toast.style.transform = "translateY(0)";
    });

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(10px)";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
window.showToast = showToast;



// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof hidePinLockModal !== 'undefined') window.hidePinLockModal = hidePinLockModal;
if (typeof setupPinSecurityUI !== 'undefined') window.setupPinSecurityUI = setupPinSecurityUI;
if (typeof showPinLockModal !== 'undefined') window.showPinLockModal = showPinLockModal;
if (typeof showToast !== 'undefined') window.showToast = showToast;
if (typeof updatePinDots !== 'undefined') window.updatePinDots = updatePinDots;