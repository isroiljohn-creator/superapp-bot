import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";

const API_BASE = import.meta.env.VITE_API_URL || "";

function getAuthHeaders(): Record<string, string> {
    const initData = (window as any).Telegram?.WebApp?.initData || "";
    return initData ? { "Authorization": `tma ${initData}` } : {};
}

const SETTING_KEYS = [
    { key: "churn_day_1", label: "Churn Day 1 (reminder)", placeholder: "Salom {name}! Sizni sog'indik..." },
    { key: "churn_day_3", label: "Churn Day 3 (value video)", placeholder: "{name}, sizga maxsus video tayyorladik..." },
    { key: "churn_day_5", label: "Churn Day 5 (discount)", placeholder: "{name}, 30% chegirma! Narx: {discounted_price}" },
    { key: "churn_day_7", label: "Churn Day 7 (farewell)", placeholder: "{name}, obunangiz tugadi..." },
    { key: "referral_reward", label: "Referal mukofoti (so'm)", placeholder: "500" },
    { key: "club_price", label: "Klub narxi (so'm)", placeholder: "97000" },
];

export default function Settings() {
    const { toast } = useToast();
    const [settings, setSettings] = useState<Record<string, string>>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState<string | null>(null);

    useEffect(() => { fetchSettings(); }, []);

    const fetchSettings = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/admin/settings`, {
                headers: getAuthHeaders(),
            });
            if (res.ok) {
                const data = await res.json();
                const map: Record<string, string> = {};
                if (Array.isArray(data)) {
                    data.forEach((s: any) => { map[s.key] = s.value; });
                } else {
                    Object.assign(map, data);
                }
                setSettings(map);
            }
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    const saveSetting = async (key: string) => {
        setSaving(key);
        try {
            const res = await fetch(`${API_BASE}/api/admin/settings/${key}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    ...getAuthHeaders(),
                },
                body: JSON.stringify({ value: settings[key] || "" }),
            });
            if (res.ok) {
                toast({ title: "✅ Saqlandi", description: `${key} yangilandi` });
            }
        } catch (e) { console.error(e); }
        setSaving(null);
    };

    if (loading) return <div className="text-center py-8 text-muted-foreground">Yuklanmoqda...</div>;

    return (
        <div className="space-y-6">
            <h2 className="text-lg font-bold">⚙️ Sozlamalar</h2>

            <div className="space-y-4">
                {SETTING_KEYS.map(({ key, label, placeholder }) => (
                    <div key={key} className="bg-card border border-border/30 rounded-lg p-4 space-y-2">
                        <label className="text-sm font-medium text-foreground">{label}</label>
                        {key.startsWith("churn_") ? (
                            <textarea
                                className="w-full bg-secondary/50 border border-border/30 rounded-md p-2 text-sm min-h-[80px] resize-y"
                                placeholder={placeholder}
                                value={settings[key] || ""}
                                onChange={(e) => setSettings(prev => ({ ...prev, [key]: e.target.value }))}
                            />
                        ) : (
                            <input
                                type="text"
                                className="w-full bg-secondary/50 border border-border/30 rounded-md p-2 text-sm"
                                placeholder={placeholder}
                                value={settings[key] || ""}
                                onChange={(e) => setSettings(prev => ({ ...prev, [key]: e.target.value }))}
                            />
                        )}
                        <button
                            onClick={() => saveSetting(key)}
                            disabled={saving === key}
                            className="px-3 py-1.5 bg-primary text-primary-foreground text-xs rounded-md hover:opacity-90 disabled:opacity-50"
                        >
                            {saving === key ? "Saqlanmoqda..." : "💾 Saqlash"}
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}
