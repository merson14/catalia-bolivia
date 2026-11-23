let allMerchants = [];
let activePlanFilter = "ALL";
let editingUserId = null;
let auditLogs = (() => {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEYS.ADMIN_LOGS) || "[]");
    } catch {
        return [];
    }
})();

function logAction(actionText) {
    const now = new Date().toLocaleTimeString("es-BO", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
    auditLogs.unshift({ time: now, text: String(actionText || "") });
    auditLogs = auditLogs.slice(0, 30);
    localStorage.setItem(STORAGE_KEYS.ADMIN_LOGS, JSON.stringify(auditLogs));
    renderAuditLog();
}

function renderAuditLog() {
    const list = document.getElementById("audit-log-list");
    if (!list) return;

    if (!auditLogs.length) {
        list.innerHTML = `<li class="text-gray-500">Sin eventos registrados aún.</li>`;
        return;
    }

    list.innerHTML = auditLogs
        .map(
            (item) => `
        <li class="flex items-center space-x-3 bg-gray-900/70 border border-gray-800 rounded-xl px-3.5 py-2">
            <span class="font-mono text-[11px] text-purple-400">[${escapeHtml(item.time)}]</span>
            <span class="text-gray-200">${escapeHtml(item.text)}</span>
        </li>
    `
        )
        .join("");
}

function clearAuditLog() {
    auditLogs = [];
    localStorage.removeItem(STORAGE_KEYS.ADMIN_LOGS);
    renderAuditLog();
}

function scrollToAuditLog() {
    document.getElementById("audit-log-section")?.scrollIntoView({ behavior: "smooth" });
}

async function loadAdminOverview(auditReason = null) {
    try {
        const data = await requestJson("/admin/overview");
        const metrics = data.metrics || {};
        allMerchants = Array.isArray(data.merchants_list) ? data.merchants_list : [];

        const paidCount = allMerchants.filter((m) => m.plan_type && m.plan_type !== "free").length;

        document.getElementById("kpi-merchants").textContent = metrics.total_merchants ?? 0;
        document.getElementById("kpi-paid").textContent = paidCount;
        document.getElementById("kpi-products").textContent = metrics.total_products ?? 0;
        document.getElementById("kpi-flyers").textContent = metrics.total_flyers_generated ?? 0;
        document.getElementById("kpi-revenue").textContent = `${Number(
            metrics.estimated_monthly_revenue_bs || 0
        ).toFixed(2)} Bs`;

        updateReportSummary();
        applyFilters();

        if (auditReason) {
            logAction(auditReason);
        }
    } catch (err) {
        console.error("Error cargando panel gerencial:", err);
        const tbody = document.getElementById("admin-merchants-tbody");
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-red-400">Error al conectar con la API de gerencia.</td></tr>`;
        }
    }
}

function toggleReportPanel() {
    const panel = document.getElementById("report-panel");
    if (!panel) return;
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden")) {
        updateReportSummary();
        panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
        logAction("Visualizó el reporte ejecutivo de cartera y planes");
    }
}

function updateReportSummary() {
    const freeCount = allMerchants.filter((m) => !m.plan_type || m.plan_type === "free").length;
    const proCount = allMerchants.filter((m) => m.plan_type === "pro_50bs").length;
    const campanaCount = allMerchants.filter((m) => m.plan_type === "campana").length;

    const proRev = proCount * PLAN_CONFIG.pro_50bs.priceBs;
    const campanaRev = campanaCount * PLAN_CONFIG.campana.priceBs;

    const breakdownEl = document.getElementById("report-plan-breakdown");
    if (breakdownEl) {
        breakdownEl.innerHTML = `
            <div class="flex justify-between items-center py-1 border-b border-gray-800">
                <span class="text-purple-300 font-medium">Freemium (0 Bs)</span>
                <span class="font-bold text-white">${freeCount} comercios</span>
            </div>
            <div class="flex justify-between items-center py-1 border-b border-gray-800">
                <span class="text-emerald-300 font-medium">Comercio Pro (${PLAN_CONFIG.pro_50bs.priceBs} Bs)</span>
                <span class="font-bold text-emerald-400">${proCount} · ${proRev.toFixed(0)} Bs</span>
            </div>
            <div class="flex justify-between items-center py-1">
                <span class="text-amber-300 font-medium">Campaña (${PLAN_CONFIG.campana.priceBs} Bs)</span>
                <span class="font-bold text-amber-400">${campanaCount} · ${campanaRev.toFixed(0)} Bs</span>
            </div>
        `;
    }

    const topProd = [...allMerchants].sort((a, b) => (b.products_count || 0) - (a.products_count || 0))[0];
    const topFlyer = [...allMerchants].sort((a, b) => (b.flyers_generated || 0) - (a.flyers_generated || 0))[0];

    document.getElementById("report-top-products").textContent = topProd
        ? `${topProd.business_name || "Comercio"} (${topProd.products_count || 0} prod.)`
        : "Sin datos";

    document.getElementById("report-top-flyers").textContent = topFlyer
        ? `${topFlyer.business_name || "Comercio"} (${topFlyer.flyers_generated || 0} flyers)`
        : "Sin datos";
}

function setPlanFilter(plan) {
    activePlanFilter = plan;
    document.querySelectorAll(".plan-btn").forEach((btn) => {
        const isSelected = btn.dataset.plan === plan;
        btn.className = isSelected
            ? "plan-btn bg-purple-600 text-white text-xs font-bold px-3.5 py-2 rounded-xl transition"
            : "plan-btn bg-gray-900 hover:bg-gray-700 text-gray-300 border border-gray-700 text-xs font-semibold px-3.5 py-2 rounded-xl transition";
    });
    applyFilters();
}

function applyFilters() {
    const term = (document.getElementById("search-merchant")?.value || "").trim().toLowerCase();

    const filtered = allMerchants.filter((m) => {
        const matchesPlan = activePlanFilter === "ALL" || m.plan_type === activePlanFilter;
        const matchesText =
            !term ||
            (m.business_name || "").toLowerCase().includes(term) ||
            (m.email || "").toLowerCase().includes(term) ||
            (m.whatsapp || "").toLowerCase().includes(term);
        return matchesPlan && matchesText;
    });

    const countEl = document.getElementById("filtered-count");
    if (countEl) {
        countEl.textContent = `Mostrando ${filtered.length} de ${allMerchants.length} comercios`;
    }
    renderMerchants(filtered);
}

function getPlanBadge(plan) {
    if (plan === "pro_50bs") {
        return `<span class="inline-block whitespace-nowrap bg-emerald-950 text-emerald-300 border border-emerald-700 text-[11px] px-2.5 py-1 rounded-full uppercase font-semibold">Comercio Pro</span>`;
    }
    if (plan === "campana") {
        return `<span class="inline-block whitespace-nowrap bg-amber-950 text-amber-300 border border-amber-700 text-[11px] px-2.5 py-1 rounded-full uppercase font-semibold">Campaña</span>`;
    }
    return `<span class="inline-block whitespace-nowrap bg-purple-950 text-purple-300 border border-purple-800 text-[11px] px-2.5 py-1 rounded-full uppercase font-semibold">Freemium</span>`;
}

function openMerchantCrm(userId) {
    const merchant = allMerchants.find((u) => Number(u.id) === Number(userId));
    if (!merchant) return;

    setImpersonatedUser(merchant);
    logAction(`Abrió el CRM Comerciante de "${merchant.business_name}"`);
    window.location.href = `dashboard.html?user_id=${encodeURIComponent(merchant.id)}`;
}

function openEditUserModal(userId) {
    const merchant = allMerchants.find((u) => Number(u.id) === Number(userId));
    if (!merchant) return;

    editingUserId = merchant.id;
    document.getElementById("edit-user-business").value = merchant.business_name || "";
    document.getElementById("edit-user-whatsapp").value = merchant.whatsapp || "";
    document.getElementById("edit-user-email").value = merchant.email || "";
    document.getElementById("edit-user-plan").value = merchant.plan_type || "free";
    document.getElementById("edit-user-flyers").value = merchant.flyers_generated ?? 0;

    const modal = document.getElementById("edit-user-modal");
    modal?.classList.remove("hidden");
    modal?.classList.add("flex");
}

function closeEditUserModal() {
    editingUserId = null;
    const modal = document.getElementById("edit-user-modal");
    modal?.classList.add("hidden");
    modal?.classList.remove("flex");
}

async function handleUpdateUser(e) {
    e.preventDefault();
    if (!editingUserId) return;

    const btn = document.getElementById("btn-save-edit-user");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "Guardando...";
    }

    const business_name = document.getElementById("edit-user-business")?.value.trim() || "";
    const rawWa = document.getElementById("edit-user-whatsapp")?.value || "";
    const whatsapp = rawWa.trim() ? formatInternationalWhatsapp("591", rawWa) : "";
    const email = document.getElementById("edit-user-email")?.value.trim() || "";
    const plan_type = document.getElementById("edit-user-plan")?.value || "free";
    const flyers_generated = Math.max(0, parseInt(document.getElementById("edit-user-flyers")?.value || "0", 10) || 0);

    try {
        await requestJson(`/admin/users/${encodeURIComponent(editingUserId)}`, {
            method: "PUT",
            body: JSON.stringify({
                business_name,
                email,
                whatsapp,
                plan_type,
                flyers_generated
            })
        });

        closeEditUserModal();
        await loadAdminOverview(`Editó datos de "${business_name}" (WA: ${whatsapp || "sin número"})`);
        alert(`✅ Datos de "${business_name}" actualizados.`);
    } catch (err) {
        alert(`Error al actualizar cliente: ${err.message}`);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = "Guardar Cambios";
        }
    }
}

function renderMerchants(merchants) {
    const tbody = document.getElementById("admin-merchants-tbody");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (!merchants.length) {
        tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-gray-500">No se encontraron comercios con los filtros seleccionados.</td></tr>`;
        return;
    }

    merchants.forEach((m, idx) => {
        const waClean = String(m.whatsapp || "").replace(/\D/g, "");
        const tr = document.createElement("tr");
        tr.className = "hover:bg-gray-800/80 transition";

        tr.innerHTML = `
            <td class="p-4">
                <div class="font-bold text-white">${escapeHtml(m.business_name || "Sin nombre")}</div>
                <div class="text-[11px] text-gray-500">Nro. #${idx + 1}</div>
            </td>
            <td class="p-4">
                <div class="flex items-center space-x-2">
                    <span class="text-gray-300 text-xs">${escapeHtml(m.email || "-")}</span>
                    <button type="button" class="copy-email-btn text-[11px] bg-gray-900 hover:bg-gray-700 text-purple-300 border border-gray-700 px-2 py-0.5 rounded-lg transition" title="Copiar correo">
                        📋
                    </button>
                </div>
                <div class="text-[11px] mt-1 ${waClean ? "text-emerald-400 font-medium" : "text-gray-500"}">
                    ${waClean ? `WA: +${escapeHtml(waClean)}` : "Sin WhatsApp registrado"}
                </div>
            </td>
            <td class="p-4">${getPlanBadge(m.plan_type)}</td>
            <td class="p-4 font-semibold text-gray-200">${escapeHtml(m.products_count ?? 0)}</td>
            <td class="p-4 font-semibold text-gray-200">${escapeHtml(m.flyers_generated ?? 0)}</td>
            <td class="p-4 text-right">
                <div class="inline-flex flex-wrap justify-end items-center gap-1.5">
                    <button type="button" class="crm-btn bg-purple-600/85 hover:bg-purple-600 text-white text-xs font-bold px-2.5 py-1.5 rounded-lg transition border border-purple-500/40">
                        CRM ↗
                    </button>
                    <a href="catalog.html?user_id=${encodeURIComponent(m.id)}" target="_blank" rel="noopener noreferrer"
                        class="bg-gray-900 hover:bg-gray-700 text-emerald-300 border border-gray-700 text-xs font-semibold px-2.5 py-1.5 rounded-lg transition">
                        Catálogo ↗
                    </a>
                    <button type="button" class="edit-btn bg-sky-950/80 hover:bg-sky-900 text-sky-300 border border-sky-700/70 text-xs font-bold px-2.5 py-1.5 rounded-lg transition">
                        ✏️ Editar
                    </button>
                    <button type="button" class="delete-btn bg-red-950/70 hover:bg-red-900 text-red-300 border border-red-800/70 text-xs font-bold px-2.5 py-1.5 rounded-lg transition">
                        Eliminar
                    </button>
                </div>
            </td>
        `;

        tr.querySelector(".copy-email-btn")?.addEventListener("click", () => copyEmail(m.email || ""));
        tr.querySelector(".crm-btn")?.addEventListener("click", () => openMerchantCrm(m.id));
        tr.querySelector(".edit-btn")?.addEventListener("click", () => openEditUserModal(m.id));
        tr.querySelector(".delete-btn")?.addEventListener("click", () =>
            deleteMerchant(m.id, m.business_name || "Comercio", m.products_count ?? 0)
        );

        tbody.appendChild(tr);
    });
}

function copyEmail(email) {
    if (!email) return;
    if (navigator.clipboard?.writeText) {
        navigator.clipboard
            .writeText(email)
            .then(() => alert(`Correo copiado: ${email}`))
            .catch(() => alert(`Correo: ${email}`));
    } else {
        alert(`Correo: ${email}`);
    }
}

function openAddUserModal() {
    document.getElementById("add-user-form")?.reset();
    const modal = document.getElementById("add-user-modal");
    modal?.classList.remove("hidden");
    modal?.classList.add("flex");
}

function closeAddUserModal() {
    const modal = document.getElementById("add-user-modal");
    modal?.classList.add("hidden");
    modal?.classList.remove("flex");
}

async function handleCreateUser(e) {
    e.preventDefault();
    const btn = document.getElementById("btn-create-user");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "Guardando...";
    }

    const business_name = document.getElementById("new-user-business")?.value.trim() || "";
    const rawWa = document.getElementById("new-user-whatsapp")?.value || "";
    const whatsapp = rawWa.trim() ? formatInternationalWhatsapp("591", rawWa) : "";
    const email = document.getElementById("new-user-email")?.value.trim() || "";
    const password = document.getElementById("new-user-password")?.value || "";
    const plan_type = document.getElementById("new-user-plan")?.value || "free";

    try {
        const created = await requestJson("/register", {
            method: "POST",
            body: JSON.stringify({ business_name, email, password, whatsapp, plan_type })
        });

        if (plan_type !== "free" && created?.id) {
            await requestJson(`/admin/users/${encodeURIComponent(created.id)}/plan?new_plan=${encodeURIComponent(plan_type)}`, {
                method: "PUT"
            });
        }

        closeAddUserModal();
        await loadAdminOverview(`Agregó usuario "${business_name}" (${email}) con plan "${plan_type}"`);
        alert(`✨ Usuario "${business_name}" creado correctamente.`);
    } catch (err) {
        alert(`Error al agregar usuario: ${err.message}`);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = "Guardar Usuario";
        }
    }
}

async function deleteMerchant(userId, businessName, productsCount) {
    const msg = `¿Seguro que deseas eliminar a "${businessName}"?\nSe eliminarán también ${productsCount} producto(s) asociados en la base de datos.`;
    if (!confirm(msg)) return;

    try {
        const data = await requestJson(`/admin/users/${encodeURIComponent(userId)}`, {
            method: "DELETE"
        });
        await loadAdminOverview(`Eliminó comercio "${businessName}" y sus ${productsCount} producto(s)`);
        alert(`🗑 ${data.message || "Comercio eliminado"}`);
    } catch (err) {
        alert(`Error al eliminar: ${err.message}`);
    }
}

window.addEventListener("DOMContentLoaded", () => {
    clearImpersonationAndRestoreAdmin();
    renderAuditLog();
    loadAdminOverview();
});