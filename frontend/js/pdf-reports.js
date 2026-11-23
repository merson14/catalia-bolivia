function downloadCsvReport(merchants = [], onLog = null) {
    const headers = ["ID", "Comercio", "Correo", "WhatsApp", "Plan", "Productos", "Flyers"];
    const rows = (merchants || []).map((m) => [
        m.id,
        `"${(m.business_name || "").replace(/"/g, '""')}"`,
        `"${(m.email || "").replace(/"/g, '""')}"`,
        `"${(m.whatsapp || "").replace(/"/g, '""')}"`,
        m.plan_type || "free",
        m.products_count ?? 0,
        m.flyers_generated ?? 0
    ]);

    const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const fileName = `reporte_catalia_crm_${new Date().toISOString().slice(0, 10)}.csv`;

    link.href = url;
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    if (typeof onLog === "function") {
        onLog(`Exportó reporte CSV con ${(merchants || []).length} comercios (${fileName})`);
    }
}

async function loadImageAsDataUrl(url) {
    return new Promise((resolve) => {
        const img = new Image();
        img.crossOrigin = "Anonymous";
        img.onload = () => {
            const canvas = document.createElement("canvas");
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(img, 0, 0);
            resolve({
                dataUrl: canvas.toDataURL("image/png"),
                ratio: img.naturalHeight / img.naturalWidth
            });
        };
        img.onerror = () => resolve(null);
        img.src = url;
    });
}

async function exportAdminPdfReport(merchants = [], onLog = null) {
    if (!window.jspdf || !window.jspdf.jsPDF) {
        alert("No se cargó jsPDF. Verifica tu conexión a internet para el CDN.");
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const fechaEmision = new Date().toLocaleString("es-BO");

    doc.setFillColor(24, 10, 46);
    doc.rect(0, 0, pageWidth, 34, "F");

    const logoAsset = await loadImageAsDataUrl("/static/logo-catalia.png");
    if (logoAsset) {
        const logoW = 42;
        const logoH = Math.min(24, logoW * logoAsset.ratio);
        doc.addImage(logoAsset.dataUrl, "PNG", 14, 5, logoW, logoH);
    } else {
        doc.setTextColor(192, 132, 252);
        doc.setFont("helvetica", "bold");
        doc.setFontSize(16);
        doc.text("CataliA BOLIVIA", 14, 17);
    }

    doc.setTextColor(255, 255, 255);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(13);
    doc.text("REPORTE GERENCIAL Y FINANCIERO", pageWidth - 14, 14, { align: "right" });

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(216, 180, 254);
    doc.text("CRM SaaS · Control de Comercios y Suscripciones", pageWidth - 14, 20, { align: "right" });
    doc.text(`Emitido: ${fechaEmision}`, pageWidth - 14, 26, { align: "right" });

    const kpiMerchants = document.getElementById("kpi-merchants")?.textContent || "0";
    const kpiPaid = document.getElementById("kpi-paid")?.textContent || "0";
    const kpiProducts = document.getElementById("kpi-products")?.textContent || "0";
    const kpiFlyers = document.getElementById("kpi-flyers")?.textContent || "0";
    const kpiRevenue = document.getElementById("kpi-revenue")?.textContent || "0 Bs";

    doc.setTextColor(30, 41, 59);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(10);
    doc.text("Resumen Ejecutivo de Métricas", 14, 44);

    doc.setFillColor(248, 250, 252);
    doc.setDrawColor(203, 213, 225);
    doc.roundedRect(14, 47, pageWidth - 28, 18, 3, 3, "FD");

    doc.setFontSize(8.5);
    doc.setTextColor(71, 85, 105);
    doc.text(`Comercios: ${kpiMerchants}`, 19, 55);
    doc.text(`De Pago: ${kpiPaid}`, 56, 55);
    doc.text(`Productos: ${kpiProducts}`, 88, 55);
    doc.text(`Flyers: ${kpiFlyers}`, 122, 55);

    doc.setTextColor(22, 163, 74);
    doc.setFont("helvetica", "bold");
    doc.text(`Ingreso Est.: ${kpiRevenue}`, 19, 61.5);

    const tableRows = (merchants || []).map((m, idx) => [
        `#${idx + 1}`,
        m.business_name || "Sin nombre",
        m.email || "-",
        m.whatsapp ? `+${m.whatsapp}` : "-",
        (m.plan_type || "free").toUpperCase(),
        String(m.products_count ?? 0),
        String(m.flyers_generated ?? 0)
    ]);

    doc.autoTable({
        startY: 72,
        head: [["Nro.", "Comercio / Importadora", "Correo", "WhatsApp", "Plan", "Prod.", "Flyers"]],
        body: tableRows.length ? tableRows : [["-", "Sin comercios registrados", "-", "-", "-", "0", "0"]],
        theme: "grid",
        styles: {
            fontSize: 8,
            cellPadding: 2.5,
            textColor: [30, 41, 59]
        },
        headStyles: {
            fillColor: [88, 28, 135],
            textColor: [255, 255, 255],
            fontStyle: "bold"
        },
        alternateRowStyles: {
            fillColor: [248, 250, 252]
        },
        margin: { left: 14, right: 14 }
    });

    const totalPages = doc.internal.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(100, 116, 139);
        doc.text(
            `CataliA Bolivia · Tecnología que impulsa tu comercio — Página ${i} de ${totalPages}`,
            pageWidth / 2,
            pageHeight - 8,
            { align: "center" }
        );
    }

    const fileName = `reporte_catalia_bolivia_${new Date().toISOString().slice(0, 10)}.pdf`;
    doc.save(fileName);

    if (typeof onLog === "function") {
        onLog(`Exportó reporte ejecutivo en PDF (${fileName})`);
    }
}