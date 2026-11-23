const API_URL = "/api";

async function requestJson(endpoint, options = {}) {
    const isFormData = options.body instanceof FormData;
    const headers = {
        ...(isFormData ? {} : { "Content-Type": "application/json" }),
        ...(options.headers || {})
    };

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers
    });

    let data = null;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
        data = await response.json();
    } else {
        const text = await response.text();
        data = text ? { detail: text } : {};
    }

    if (!response.ok) {
        throw new Error(data?.detail || `Error HTTP ${response.status}`);
    }

    return data;
}