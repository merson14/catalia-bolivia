function switchTab(tab) {
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const tabLogin = document.getElementById("tab-login");
    const tabRegister = document.getElementById("tab-register");
    const errorBox = document.getElementById("auth-error");

    if (errorBox) errorBox.classList.add("hidden");

    if (tab === "login") {
        loginForm?.classList.remove("hidden");
        registerForm?.classList.add("hidden");
        tabLogin?.classList.add("text-purple-400", "border-b-2", "border-purple-400");
        tabLogin?.classList.remove("text-gray-400");
        tabRegister?.classList.remove("text-purple-400", "border-b-2", "border-purple-400");
        tabRegister?.classList.add("text-gray-400");
    } else {
        registerForm?.classList.remove("hidden");
        loginForm?.classList.add("hidden");
        tabRegister?.classList.add("text-purple-400", "border-b-2", "border-purple-400");
        tabRegister?.classList.remove("text-gray-400");
        tabLogin?.classList.remove("text-purple-400", "border-b-2", "border-purple-400");
        tabLogin?.classList.add("text-gray-400");
    }
}

function togglePaymentSection() {
    const plan = document.getElementById("reg-plan")?.value || "free";
    const paymentBox = document.getElementById("payment-sim-box");
    const amountLabel = document.getElementById("payment-amount-label");

    if (!paymentBox) return;

    if (plan === "free") {
        paymentBox.classList.add("hidden");
        return;
    }

    paymentBox.classList.remove("hidden");
    if (amountLabel) {
        const cfg = PLAN_CONFIG[plan] || PLAN_CONFIG.pro_50bs;
        amountLabel.textContent = `${cfg.priceBs.toFixed(2)} Bs${cfg.period}`;
    }
}

function switchPaymentMethod(method) {
    const qrBox = document.getElementById("pay-method-qr");
    const cardBox = document.getElementById("pay-method-card");
    const btnQr = document.getElementById("btn-pay-qr");
    const btnCard = document.getElementById("btn-pay-card");

    if (method === "qr") {
        qrBox?.classList.remove("hidden");
        cardBox?.classList.add("hidden");
        btnQr?.classList.add("bg-purple-600", "text-white");
        btnQr?.classList.remove("bg-gray-800", "text-gray-300");
        btnCard?.classList.remove("bg-purple-600", "text-white");
        btnCard?.classList.add("bg-gray-800", "text-gray-300");
    } else {
        cardBox?.classList.remove("hidden");
        qrBox?.classList.add("hidden");
        btnCard?.classList.add("bg-purple-600", "text-white");
        btnCard?.classList.remove("bg-gray-800", "text-gray-300");
        btnQr?.classList.remove("bg-purple-600", "text-white");
        btnQr?.classList.add("bg-gray-800", "text-gray-300");
    }
}

function showAuthError(message) {
    const errorBox = document.getElementById("auth-error");
    if (!errorBox) return;
    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
}

function redirectAfterAuth(user) {
    setStoredUser(user);
    if (user.email === "admin@catalia.bo") {
        window.location.href = "admin.html";
    } else {
        window.location.href = "dashboard.html";
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById("login-email")?.value.trim() || "";
    const password = document.getElementById("login-password")?.value || "";

    try {
        const user = await requestJson("/login", {
            method: "POST",
            body: JSON.stringify({ email, password })
        });
        redirectAfterAuth(user);
    } catch (err) {
        showAuthError(err.message || "Error al iniciar sesión.");
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const business_name = document.getElementById("reg-business")?.value.trim() || "";
    const countryCode = document.getElementById("reg-country-code")?.value || "591";
    const rawWhatsapp = document.getElementById("reg-whatsapp")?.value || "";
    const whatsapp = formatInternationalWhatsapp(countryCode, rawWhatsapp);
    const email = document.getElementById("reg-email")?.value.trim() || "";
    const password = document.getElementById("reg-password")?.value || "";
    const plan_type = document.getElementById("reg-plan")?.value || "free";

    try {
        const created = await requestJson("/register", {
            method: "POST",
            body: JSON.stringify({
                business_name,
                whatsapp,
                email,
                password,
                plan_type
            })
        });
        redirectAfterAuth(created);
    } catch (err) {
        showAuthError(err.message || "No se pudo completar el registro.");
    }
}

window.addEventListener("DOMContentLoaded", () => {
    populateCountrySelect("reg-country-code", "country-flag-icon");
    togglePaymentSection();
    switchPaymentMethod("qr");
});