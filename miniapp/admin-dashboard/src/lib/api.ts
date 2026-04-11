// src/lib/api.ts
export const API_URL = import.meta.env.VITE_API_URL || "";

/**
 * Helper to get the Telegram WebApp initData securely
 */
export function getInitData(): string {
    try {
        if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
            const data = (window as any).Telegram.WebApp.initData;
            if (data && typeof data === "string" && data.length > 0) {
                return data;
            }
        }
    } catch (e) {
        console.warn("Failed to get Telegram initData:", e);
    }
    return "";
}

/**
 * Generic JSON fetch wrapper that auto-injects auth headers
 */
export async function fetchApi(endpoint: string, options: RequestInit = {}) {
    const initData = getInitData();
    const token = typeof window !== "undefined" ? localStorage.getItem("admin_token") : null;
    const headers = new Headers(options.headers || {});

    headers.set("Content-Type", "application/json");
    
    // Priority: JWT Token first for direct browser access, then Telegram initData
    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    } else if (initData) {
        headers.set("Authorization", `tma ${initData}`);
    }

    const url = `${API_URL}${endpoint}`;
    console.log(`[API] ${options.method || "GET"} ${endpoint}`, (token || initData) ? "with auth" : "NO AUTH");

    const response = await fetch(url, {
        ...options,
        headers,
    });

    const text = await response.text();

    if (!response.ok) {
        let errorDetail = `HTTP ${response.status}`;
        try {
            const errorData = JSON.parse(text);
            errorDetail = errorData.detail || errorDetail;
        } catch { }
        console.error(`[API] Error ${response.status} on ${endpoint}:`, errorDetail);
        throw new Error(errorDetail);
    }

    try {
        return JSON.parse(text);
    } catch {
        return text;
    }
}
