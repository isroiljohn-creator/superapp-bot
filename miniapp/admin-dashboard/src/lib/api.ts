// src/lib/api.ts
export const API_URL = import.meta.env.VITE_API_URL || "";

/**
 * Helper to get the Telegram WebApp initData securely
 */
export function getInitData(): string {
    if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
        return (window as any).Telegram.WebApp.initData || "";
    }
    return "";
}

/**
 * Generic JSON fetch wrapper that auto-injects auth headers
 */
export async function fetchApi(endpoint: string, options: RequestInit = {}) {
    const initData = getInitData();
    const headers = new Headers(options.headers || {});

    headers.set("Content-Type", "application/json");
    if (initData) {
        headers.set("Authorization", `tma ${initData}`);
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "API xatolik yuz berdi");
    }

    return response.json();
}
