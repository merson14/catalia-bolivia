let currentUser = null;
let currentInventory = [];
let isAdminViewingMerchant = false;

const MAX_IMAGE_BYTES = 3 * 1024 * 1024; // 3 MB

const PLACEHOLDER_IMG =
    "data:image/svg+xml;utf8," +
    encodeURIComponent(
        `<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 160 160">
            <rect width="160" height="160" fill="#180a2e"/>
            <text x="80" y="86" text-anchor="middle" fill="#c084fc" font-family="Arial, sans-serif" font-size="16" font-weight="bold">CataliA</text>
        </svg>`
    );

function getPlanLabel(planType) {
    return PLAN_CONFIG[planType]?.label || PLAN_CONFIG.free.label;
}

function showAdminImpersonationBar(businessName) {
    const mainEl = document.querySelector("main");
    if (!mainEl || document.getElementById("admin-impersonation-banner")) return;

    const banner = document.createElement("div");
    banner.id = "admin-impersonation-banner";
    banner.className =
        "mb-6 bg-amber-950/70 border border-amber-600/50 text-amber-200 px-4 py-3 rounded-2xl flex flex-wrap items-center justify-between gap-3 text-xs";
    banner.innerHTML = `
        <span>👁️ <strong>Modo Admin:</strong> Viendo el CRM del comercio <strong>${escapeHtml(businessName || "Cliente")}</strong>.</span>
        <button type="button" id="btn-return-admin" class="bg-amber-500 hover:bg-amber-400 text-gray-950 font-extrabold px-3 py-1.5 rounded-xl transition">
            ← Volver al Panel Admin
        </button>
    `;
    banner.querySelector("#btn-return-admin")?.addEventListener("click", returnToAdminPanel);
    mainEl.prepend(banner);
}

function returnToAdminPanel() {
    clearImpersonationAndRestoreAdmin();
    window.location.href = "admin.html";
}

async function resolveActiveMerchant() {
    const params = new URLSearchParams(window.location.search);
    const queryUserId = params.get("user_id");
    const impersonated = getImpersonatedUser();

    if (queryUserId) {
        if (impersonated && String(impersonated.id) === String(queryUserId)) {
            isAdminViewingMerchant = true;
            return impersonated;
        }
        try {
            const users = await requestJson("/admin/users");
            const found = (Array.isArray(users) ? users : []).find((u) => String(u.id) === String(queryUserId));
            if (found) {
                isAdminViewingMerchant = true;
                setImpersonatedUser(found);
                return found;
            }
        } catch (err) {
            console.warn("No se pudo resolver user_id desde admin:", err);
        }
    }

    return getStoredUser();
}

function updateMerchantNavigation() {
    if (!currentUser) return;
    const displayName = currentUser.business_name || currentUser.email || "Comerciante";
    const nameEl = document.getElementById("user-display-name");
    if (nameEl) nameEl.textContent = displayName;

    const planEl = document.getElementById("user-plan-label");
    if (planEl) planEl.textContent = getPlanLabel(currentUser.plan_type);

    const catalogUrl = isAdminViewingMerchant
        ? `catalog.html?user_id=${encodeURIComponent(currentUser.id)}`
        : "catalog.html";

    document.querySelectorAll('a[href="catalog.html"]').forEach((link) => {
        link.setAttribute("href", catalogUrl);
    });
}

async function loadInventory() {
    if (!currentUser) return;

    try {
        const data = await requestJson(`/products/${encodeURIComponent(currentUser.id)}`);
        currentInventory = Array.isArray(data) ? data : [];

        const prodKpi = document.getElementById("kpi-products");
        if (prodKpi) prodKpi.textContent = currentInventory.length;

        try {
            const stats = await requestJson(`/flyers/count/${encodeURIComponent(currentUser.id)}`);
            const flyerCount = stats?.flyers_generated ?? stats?.count ?? 0;
            const flyerKpi = document.getElementById("kpi-flyers");
            if (flyerKpi) flyerKpi.textContent = flyerCount;
        } catch {
            // Mantiene el conteo actual si falla el endpoint auxiliar
        }

        renderInventoryTable(currentInventory);
    } catch (err) {
        console.error("Error cargando inventario:", err);
        const tbody = document.getElementById("inventory-tbody");
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="5" class="p-8 text-center text-red-400">Error al cargar el inventario.</td></tr>`;
        }
    }
}

function renderInventoryTable(products) {
    const tbody = document.getElementById("inventory-tbody");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (!products.length) {
        tbody.innerHTML = `<tr><td colspan="5" class="p-8 text-center text-gray-500">No tienes productos digitalizados todavía. ¡Crea el primero arriba!</td></tr>`;
        return;
    }

    products.forEach((p) => {
        const imgSrc = p.image_data || PLACEHOLDER_IMG;
        const firstUrgency = p.urgency_phrase ? p.urgency_phrase.split("||")[0].trim() : "Oferta";
        const tr = document.createElement("tr");
        tr.className = "hover:bg-gray-800/50 transition";

        tr.innerHTML = `
            <td class="p-4 flex items-center space-x-3">
                <div class="w-12 h-12 bg-black/60 rounded-xl border border-gray-700 overflow-hidden flex-shrink-0">
                    <img src="${escapeHtml(imgSrc)}" alt="${escapeHtml(p.name || "Producto")}" class="w-full h-full object-cover">
                </div>
                <div>
                    <span class="font-bold text-white block">${escapeHtml(p.name || "Producto")}</span>
                    <span class="text-[11px] text-purple-400 font-medium">"${escapeHtml(firstUrgency)}"</span>
                </div>
            </td>
            <td class="p-4">
                <span class="bg-purple-950/80 text-purple-300 border border-purple-800/60 text-xs px-2.5 py-1 rounded-full font-semibold">
                    ${escapeHtml(p.category || "General")}
                </span>
            </td>
            <td class="p-4 max-w-xs">
                <p class="text-xs text-gray-300 mb-1">${escapeHtml(p.commercial_description || "")}</p>
                <p class="text-[11px] text-emerald-400 font-medium bg-emerald-950/30 border border-emerald-900/40 p-2 rounded-lg">
                    💡 <strong>Estrategia:</strong> ${escapeHtml(p.estrategia_promocion || "Destacar durabilidad y utilidad directa.")}
                </p>
            </td>
            <td class="p-4 font-black text-emerald-400">${escapeHtml(p.price)} ${escapeHtml(p.currency || "Bs")}</td>
            <td class="p-4 text-right space-x-1">
                <button type="button" class="flyer-btn bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold px-3 py-2 rounded-xl transition shadow-md" title="Generar Banner PromoFlash">
                    ⚡ Flyer
                </button>
                <button type="button" class="del-prod-btn bg-red-950/60 hover:bg-red-900 text-red-300 border border-red-800/60 text-xs font-bold px-2.5 py-2 rounded-xl transition" title="Eliminar producto">
                    ✕
                </button>
            </td>
        `;

        const imgEl = tr.querySelector("img");
        imgEl?.addEventListener("error", () => {
            if (imgEl.src !== PLACEHOLDER_IMG) imgEl.src = PLACEHOLDER_IMG;
        });

        tr.querySelector(".flyer-btn")?.addEventListener("click", () => openPromoFlashById(p.id));
        tr.querySelector(".del-prod-btn")?.addEventListener("click", () => deleteProduct(p.id));

        tbody.appendChild(tr);
    });
}

const toBase64 = (file) =>
    new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = (error) => reject(error);
    });

async function handleProductSubmit(e) {
    e.preventDefault();
    if (!currentUser) return;

    const btn = document.getElementById("btn-process");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "Analizando con IA...";
    }

    const name = document.getElementById("prod-name")?.value.trim() || "";
    const price = parseFloat(document.getElementById("prod-price")?.value || "0");
    const fileInput = document.getElementById("prod-file");

    if (!name || Number.isNaN(price) || price < 0) {
        alert("Ingresa un nombre de producto y un precio válido.");
        if (btn) {
            btn.disabled = false;
            btn.textContent = "Procesar con IA 🚀";
        }
        return;
    }

    let imageData = null;
    if (fileInput && fileInput.files && fileInput.files.length > 0) {
        const file = fileInput.files[0];
        if (!file.type.startsWith("image/")) {
            alert("Selecciona un archivo de imagen válido.");
            if (btn) {
                btn.disabled = false;
                btn.textContent = "Procesar con IA 🚀";
            }
            return;
        }
        if (file.size > MAX_IMAGE_BYTES) {
            alert("La imagen supera el límite de 3 MB.");
            if (btn) {
                btn.disabled = false;
                btn.textContent = "Procesar con IA 🚀";
            }
            return;
        }
        imageData = await toBase64(file);
    }

    try {
        await requestJson(`/products/${encodeURIComponent(currentUser.id)}`, {
            method: "POST",
            body: JSON.stringify({ name, price, currency: "Bs", image_data: imageData })
        });

        document.getElementById("product-form")?.reset();
        await loadInventory();
    } catch (err) {
        alert(err.message || "Error al registrar el producto con IA.");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = "Procesar con IA 🚀";
        }
    }
}

function openPromoFlashById(id) {
    const product = currentInventory.find((p) => Number(p.id) === Number(id));
    if (product) {
        localStorage.setItem("catalia_selected_product", JSON.stringify(product));
        window.location.href = "promoflash.html";
    }
}

async function deleteProduct(id) {
    if (!confirm("¿Deseas eliminar este producto del inventario?")) return;
    try {
        await requestJson(`/products/${encodeURIComponent(id)}`, { method: "DELETE" });
        await loadInventory();
    } catch (err) {
        alert(err.message || "Error al eliminar el producto.");
    }
}

async function exportMerchantCatalogPdf() {
    if (!window.jspdf || !window.jspdf.jsPDF) {
        alert("No se cargó jsPDF. Verifica tu conexión a internet para el CDN.");
        return;
    }

    if (!currentInventory || currentInventory.length === 0) {
        alert("No tienes productos en tu inventario para exportar en PDF.");
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const businessName = currentUser?.business_name || currentUser?.email || "Comercio CataliA";
    const fechaEmision = new Date().toLocaleString("es-BO");

    const preparedImages = await Promise.all(
        currentInventory.map((p) => loadImageAsDataUrl(p.image_data || PLACEHOLDER_IMG))
    );

    doc.setFillColor(24, 10, 46);
    doc.rect(0, 0, pageWidth, 36, "F");

    const logoAsset = await loadImageAsDataUrl("/static/logo-catalia.png");
    if (logoAsset) {
        const logoW = 40;
        const logoH = Math.min(24, logoW * logoAsset.ratio);
        doc.addImage(logoAsset.dataUrl, logoAsset.format, 14, 6, logoW, logoH);
    } else {
        doc.setTextColor(192, 132, 252);
        doc.setFont("helvetica", "bold");
        doc.setFontSize(15);
        doc.text("CataliA BOLIVIA", 14, 18);
    }

    doc.setTextColor(255, 255, 255);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(13);
    doc.text(businessName.toUpperCase(), pageWidth - 14, 14, { align: "right" });

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(110, 231, 183);
    doc.text(`Catálogo Comercial · ${currentInventory.length} producto(s)`, pageWidth - 14, 21, { align: "right" });
    doc.setTextColor(216, 180, 254);
    doc.text(`Fecha: ${fechaEmision}`, pageWidth - 14, 27, { align: "right" });

    const rows = currentInventory.map((p, idx) => [
        String(idx + 1),
        "",
        p.name || "Producto",
        p.category || "General",
        p.commercial_description || "-",
        `${p.price} ${p.currency || "Bs"}`
    ]);

    doc.autoTable({
        startY: 44,
        head: [["#", "Imagen", "Producto", "Categoría", "Descripción Comercial", "Precio"]],
        body: rows,
        theme: "grid",
        styles: {
            fontSize: 8.5,
            cellPadding: 2.5,
            textColor: [30, 41, 59],
            valign: "middle",
            minCellHeight: 22
        },
        columnStyles: {
            0: { cellWidth: 9, halign: "center" },
            1: { cellWidth: 22, halign: "center" },
            2: { cellWidth: 32, fontStyle: "bold" },
            3: { cellWidth: 25 },
            4: { cellWidth: 72 },
            5: { cellWidth: 22, halign: "right", fontStyle: "bold" }
        },
        headStyles: {
            fillColor: [88, 28, 135],
            textColor: [255, 255, 255],
            fontStyle: "bold",
            minCellHeight: 9
        },
        alternateRowStyles: {
            fillColor: [248, 250, 252]
        },
        margin: { left: 14, right: 14 },
        didDrawCell: (data) => {
            if (data.section === "body" && data.column.index === 1) {
                const asset = preparedImages[data.row.index];
                if (asset && asset.dataUrl) {
                    const maxW = data.cell.width - 4;
                    const maxH = data.cell.height - 4;
                    let drawW = maxW;
                    let drawH = drawW * asset.ratio;

                    if (drawH > maxH) {
                        drawH = maxH;
                        drawW = drawH / asset.ratio;
                    }

                    const x = data.cell.x + (data.cell.width - drawW) / 2;
                    const y = data.cell.y + (data.cell.height - drawH) / 2;

                    try {
                        doc.addImage(asset.dataUrl, asset.format, x, y, drawW, drawH);
                    } catch {}
                }
            }
        }
    });

    const totalPages = doc.internal.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(100, 116, 139);
        doc.text(
            `${businessName} · Generado con CataliA Bolivia — Página ${i} de ${totalPages}`,
            pageWidth / 2,
            pageHeight - 8,
            { align: "center" }
        );
    }

    const safeName = businessName.toLowerCase().replace(/[^a-z0-9]+/gi, "_") || "catalogo";
    doc.save(`catalogo_${safeName}_${new Date().toISOString().slice(0, 10)}.pdf`);
}

window.addEventListener("DOMContentLoaded", async () => {
    currentUser = await resolveActiveMerchant();
    if (!currentUser) {
        window.location.href = "index.html";
        return;
    }

    updateMerchantNavigation();
    if (isAdminViewingMerchant) {
        showAdminImpersonationBar(currentUser.business_name);
    }

    await loadInventory();
});