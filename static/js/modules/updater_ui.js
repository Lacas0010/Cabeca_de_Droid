// ==========================================================================
// Auto-Updater UI (GitHub Releases) integrado aos Web Components Sakuga VFX
// ==========================================================================

const DISMISSED_STORAGE_KEY = "updater_dismissed_version";
const DEFAULT_RELEASE_URL = "https://github.com/Lacas0010/Cabeca_de_Droid/releases/latest";

let _latestCheckData = null;
let _pollTimer = null;
let _isUpdating = false;

function formatVersionLabel(version) {
    const clean = String(version || "").trim().replace(/^v/i, "");
    return clean ? `v${clean}` : "v0.0.0";
}

function getModalElements() {
    return {
        badge: document.getElementById("app-version-badge"),
        checkBtn: document.getElementById("btn-check-updates"),
        modal: document.getElementById("modal-sakuga-updater"),
        verCurrent: document.getElementById("updater-ver-current"),
        verLatest: document.getElementById("updater-ver-latest"),
        notesBox: document.getElementById("updater-release-notes"),
        progressArea: document.getElementById("updater-progress-area"),
        progressBar: document.getElementById("updater-progress-bar"),
        statusText: document.getElementById("updater-status-text"),
        progressPct: document.getElementById("updater-progress-pct"),
        decisionActions: document.getElementById("updater-decision-actions"),
        btnLater: document.getElementById("btn-updater-later"),
        btnInstall: document.getElementById("btn-updater-install"),
        devNotice: document.getElementById("updater-dev-notice"),
        devMessage: document.getElementById("updater-dev-message"),
        releaseLink: document.getElementById("updater-release-link"),
        btnCloseDev: document.getElementById("btn-updater-close-dev"),
    };
}

function stopUpdatePolling() {
    if (_pollTimer !== null) {
        clearInterval(_pollTimer);
        _pollTimer = null;
    }
}

function updateProgressVisual(progress, message) {
    const els = getModalElements();
    const clamped = Math.max(0, Math.min(1, Number(progress) || 0));
    const pct = Math.round(clamped * 100);

    if (els.progressBar && typeof els.progressBar.set === "function") {
        els.progressBar.set(clamped);
    } else if (els.progressBar) {
        els.progressBar.setAttribute("value", String(clamped));
    }
    if (els.progressPct) {
        els.progressPct.textContent = `${pct}%`;
    }
    if (els.statusText && message) {
        els.statusText.textContent = message;
    }
}

function closeUpdaterModal(saveDismiss = false) {
    if (_isUpdating) return;
    stopUpdatePolling();
    const els = getModalElements();
    if (saveDismiss && _latestCheckData?.latest_version) {
        try {
            sessionStorage.setItem(DISMISSED_STORAGE_KEY, _latestCheckData.latest_version);
        } catch (_) {}
    }
    if (els.modal) {
        els.modal.style.display = "none";
    }
}

function openUpdaterModal(checkData) {
    const els = getModalElements();
    if (!els.modal || !checkData) return;

    _latestCheckData = checkData;
    _isUpdating = false;
    stopUpdatePolling();

    if (els.verCurrent) els.verCurrent.textContent = formatVersionLabel(checkData.current_version);
    if (els.verLatest) els.verLatest.textContent = formatVersionLabel(checkData.latest_version);
    if (els.notesBox) {
        const notes = String(checkData.release_notes || "").trim();
        els.notesBox.textContent = notes || "Melhorias de estabilidade, otimizações e correções gerais.";
    }
    if (els.releaseLink) {
        els.releaseLink.href = checkData.release_url || DEFAULT_RELEASE_URL;
    }

    if (els.progressArea) els.progressArea.style.display = "none";
    if (els.devNotice) els.devNotice.style.display = "none";
    if (els.decisionActions) els.decisionActions.style.display = "flex";
    if (els.btnInstall) els.btnInstall.disabled = false;
    if (els.btnLater) els.btnLater.disabled = false;

    if (els.progressBar && typeof els.progressBar.reset === "function") {
        els.progressBar.reset();
    }
    updateProgressVisual(0, "Preparando atualização...");

    els.modal.style.display = "flex";
}

function showDevModeNotice(message, releaseUrl) {
    const els = getModalElements();
    _isUpdating = false;
    stopUpdatePolling();
    if (els.progressArea) els.progressArea.style.display = "none";
    if (els.decisionActions) els.decisionActions.style.display = "none";
    if (els.devMessage) {
        els.devMessage.textContent = message || (
            "Você está executando o projeto via Python/Git. O auto-updater automático atua apenas no executável compilado (.exe)."
        );
    }
    if (els.releaseLink) {
        els.releaseLink.href = releaseUrl || _latestCheckData?.release_url || DEFAULT_RELEASE_URL;
    }
    if (els.devNotice) els.devNotice.style.display = "block";
}

async function pollUpdateStatus() {
    const els = getModalElements();
    let lastStage = "";
    let doneCelebrated = false;

    const tick = async () => {
        try {
            const res = await fetch("/api/updater/status", { cache: "no-store" });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const status = await res.json();
            lastStage = status.stage || lastStage;

            if (status.stage === "dev_mode") {
                showDevModeNotice(status.message, _latestCheckData?.release_url);
                return;
            }

            if (status.stage === "error") {
                _isUpdating = false;
                stopUpdatePolling();
                if (els.decisionActions) els.decisionActions.style.display = "flex";
                if (els.btnInstall) els.btnInstall.disabled = false;
                if (els.btnLater) els.btnLater.disabled = false;
                updateProgressVisual(status.progress || 0, status.message || "Falha ao atualizar.");
                if (typeof window.showToast === "function") {
                    window.showToast(status.message || "Erro ao aplicar atualização.", "error");
                }
                return;
            }

            updateProgressVisual(status.progress, status.message || "Atualizando...");

            if ((status.stage === "applying" || Number(status.progress) >= 1) && !doneCelebrated) {
                doneCelebrated = true;
                if (els.btnInstall && typeof els.btnInstall.done === "function") {
                    els.btnInstall.done(2.0);
                }
                if (typeof window.showToast === "function") {
                    window.showToast("Atualização concluída! Reiniciando o aplicativo...", "success");
                }
                stopUpdatePolling();
                _isUpdating = false;
                scheduleReloadAfterRestart();
            }
        } catch (_) {
            if (lastStage === "applying") {
                stopUpdatePolling();
                _isUpdating = false;
                updateProgressVisual(1, "Aplicando arquivos e reiniciando...");
                scheduleReloadAfterRestart();
            }
        }
    };

    await tick();
    if (_pollTimer === null && _isUpdating) {
        _pollTimer = setInterval(tick, 350);
    }
}

let _restartWatchStarted = false;
function scheduleReloadAfterRestart() {
    if (_restartWatchStarted) return;
    _restartWatchStarted = true;
    let tries = 0;
    const waitTimer = setInterval(async () => {
        tries += 1;
        if (tries < 3) return; // aguarda encerramento e troca do .exe
        if (tries > 20) {
            clearInterval(waitTimer);
            return;
        }
        try {
            const res = await fetch("/api/updater/check", { cache: "no-store" });
            if (res.ok) {
                clearInterval(waitTimer);
                window.location.reload();
            }
        } catch (_) {}
    }, 1500);
}

async function handleInstallClick() {
    if (_isUpdating || !_latestCheckData) return;
    const els = getModalElements();

    if (!_latestCheckData.is_frozen) {
        try {
            const res = await fetch("/api/updater/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    download_url: _latestCheckData.download_url || null,
                    target_version: _latestCheckData.latest_version || null,
                    release_url: _latestCheckData.release_url || null,
                }),
            });
            const data = await res.json();
            showDevModeNotice(data.message, _latestCheckData.release_url);
        } catch (_) {
            showDevModeNotice(null, _latestCheckData.release_url);
        }
        return;
    }

    _isUpdating = true;
    if (els.decisionActions) els.decisionActions.style.display = "none";
    if (els.progressArea) els.progressArea.style.display = "block";
    updateProgressVisual(0.05, "Iniciando download da release...");

    try {
        const res = await fetch("/api/updater/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                download_url: _latestCheckData.download_url || null,
                target_version: _latestCheckData.latest_version || null,
                release_url: _latestCheckData.release_url || null,
            }),
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || `HTTP ${res.status}`);
        }
        if (data.stage === "dev_mode") {
            showDevModeNotice(data.message, _latestCheckData.release_url);
            return;
        }
        await pollUpdateStatus();
    } catch (err) {
        _isUpdating = false;
        if (els.decisionActions) els.decisionActions.style.display = "flex";
        if (els.btnInstall) els.btnInstall.disabled = false;
        if (els.btnLater) els.btnLater.disabled = false;
        if (typeof window.showToast === "function") {
            window.showToast(`Falha ao iniciar atualização: ${err.message}`, "error");
        }
    }
}

export async function checkUpdates(manual = false) {
    const els = getModalElements();
    if (manual && els.checkBtn) {
        els.checkBtn.disabled = true;
    }

    try {
        const res = await fetch("/api/updater/check", { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        _latestCheckData = data;

        if (els.badge && data.current_version) {
            els.badge.textContent = formatVersionLabel(data.current_version);
        }

        if (data.error) {
            if (manual && typeof window.showToast === "function") {
                window.showToast(`Não foi possível checar o GitHub: ${data.error}`, "info");
            }
            return data;
        }

        if (data.update_available) {
            let dismissedVer = null;
            try {
                dismissedVer = sessionStorage.getItem(DISMISSED_STORAGE_KEY);
            } catch (_) {}

            if (manual || dismissedVer !== data.latest_version) {
                openUpdaterModal(data);
            }
            return data;
        }

        if (manual && typeof window.showToast === "function") {
            window.showToast(
                `Você já está na versão mais recente (${formatVersionLabel(data.current_version)}).`,
                "success"
            );
        }
        return data;
    } catch (_) {
        if (manual && typeof window.showToast === "function") {
            window.showToast("Sem conexão para verificar atualizações no momento.", "info");
        }
        return null;
    } finally {
        if (manual && els.checkBtn) {
            els.checkBtn.disabled = false;
        }
    }
}

export function setupUpdaterUI() {
    const els = getModalElements();

    if (els.checkBtn) {
        els.checkBtn.addEventListener("click", () => {
            checkUpdates(true);
        });
    }
    if (els.btnLater) {
        els.btnLater.addEventListener("click", () => closeUpdaterModal(true));
    }
    if (els.btnCloseDev) {
        els.btnCloseDev.addEventListener("click", () => closeUpdaterModal(true));
    }
    if (els.btnInstall) {
        els.btnInstall.addEventListener("click", handleInstallClick);
    }
    if (els.modal) {
        els.modal.addEventListener("click", (e) => {
            if (e.target === els.modal) closeUpdaterModal(false);
        });
    }
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && els.modal && els.modal.style.display === "flex") {
            closeUpdaterModal(false);
        }
    });

    // Checagem silenciosa não bloqueante ao carregar a aplicação
    checkUpdates(false);
}

window.setupUpdaterUI = setupUpdaterUI;
window.checkUpdates = checkUpdates;
