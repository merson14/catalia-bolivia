const STORAGE_KEYS = {
    USER: "catalia_user",
    IMPERSONATED: "catalia_impersonated_user",
    ADMIN_BACKUP: "catalia_admin_backup",
    ADMIN_LOGS: "catalia_admin_logs"
};

const PLAN_CONFIG = {
    free: { label: "Plan Freemium", priceBs: 0, period: "" },
    pro_50bs: { label: "Plan Comercio Pro", priceBs: 65, period: " / mes" },
    campana: { label: "Pase Campaña", priceBs: 120, period: " (Campaña)" }
};

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function getStoredUser() {
    try {
        const raw = localStorage.getItem(STORAGE_KEYS.USER);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

function setStoredUser(user) {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
}

function getImpersonatedUser() {
    try {
        const raw = localStorage.getItem(STORAGE_KEYS.IMPERSONATED);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

function setImpersonatedUser(merchant) {
    const currentSession = localStorage.getItem(STORAGE_KEYS.USER);
    if (currentSession && !localStorage.getItem(STORAGE_KEYS.ADMIN_BACKUP)) {
        localStorage.setItem(STORAGE_KEYS.ADMIN_BACKUP, currentSession);
    }
    localStorage.setItem(STORAGE_KEYS.IMPERSONATED, JSON.stringify(merchant));
}

function clearImpersonationAndRestoreAdmin() {
    localStorage.removeItem(STORAGE_KEYS.IMPERSONATED);
    const adminBackup = localStorage.getItem(STORAGE_KEYS.ADMIN_BACKUP);
    if (adminBackup) {
        localStorage.setItem(STORAGE_KEYS.USER, adminBackup);
        localStorage.removeItem(STORAGE_KEYS.ADMIN_BACKUP);
    }
}

function clearAllSessionData() {
    localStorage.removeItem(STORAGE_KEYS.USER);
    localStorage.removeItem(STORAGE_KEYS.IMPERSONATED);
    localStorage.removeItem(STORAGE_KEYS.ADMIN_BACKUP);
}

function formatInternationalWhatsapp(countryCode, rawNumber) {
    const code = String(countryCode || "591").replace(/\D/g, "");
    let number = String(rawNumber || "").replace(/\D/g, "");
    if (!number) return "";

    if (number.startsWith(code) && number.length > code.length + 5) {
        return number;
    }

    number = number.replace(/^0+/, "");
    return `${code}${number}`;
}