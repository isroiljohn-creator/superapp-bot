import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";

const API_BASE = import.meta.env.VITE_API_URL || "";

function getAuthHeaders(): Record<string, string> {
    const initData = (window as any).Telegram?.WebApp?.initData || "";
    return initData ? { "Authorization": `tma ${initData}` } : {};
}

interface Prompt {
    key: string;
    label: string;
    value: string;
    is_custom: boolean;
    default: string;
}

export default function PromptManager() {
    const { toast } = useToast();
    const [prompts, setPrompts] = useState<Prompt[]>([]);
    const [loading, setLoading] = useState(true);
    const [editingKey, setEditingKey] = useState<string | null>(null);
    const [editValue, setEditValue] = useState("");
    const [saving, setSaving] = useState(false);

    useEffect(() => { fetchPrompts(); }, []);

    const fetchPrompts = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/admin/prompts`, {
                headers: getAuthHeaders(),
            });
            if (res.ok) setPrompts(await res.json());
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    const savePrompt = async (key: string) => {
        setSaving(true);
        try {
            const res = await fetch(`${API_BASE}/api/admin/prompts`, {
                method: "PUT",
                headers: { "Content-Type": "application/json", ...getAuthHeaders() },
                body: JSON.stringify({ key, value: editValue }),
            });
            if (res.ok) {
                toast({ title: "✅ Prompt saqlandi" });
                setEditingKey(null);
                fetchPrompts();
            }
        } catch (e) { console.error(e); }
        setSaving(false);
    };

    const resetPrompt = async (key: string) => {
        try {
            const res = await fetch(`${API_BASE}/api/admin/prompts/${key}`, {
                method: "DELETE",
                headers: getAuthHeaders(),
            });
            if (res.ok) {
                toast({ title: "🔄 Standart qiymatga qaytarildi" });
                setEditingKey(null);
                fetchPrompts();
            }
        } catch (e) { console.error(e); }
    };

    if (loading) return <div className="text-center py-8 text-muted-foreground">Yuklanmoqda...</div>;

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold">🧠 AI Promtlar</h2>
            </div>
            <p className="text-xs text-muted-foreground">
                Chatbot, kopirayter va rasm yaratish uchun system promptlarni boshqaring.
                O'zgartirishlar darhol kuchga kiradi.
            </p>

            <div className="space-y-4">
                {prompts.map((p) => (
                    <div key={p.key} className="bg-card border border-border/30 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-semibold">{p.label}</span>
                            <div className="flex items-center gap-2">
                                {p.is_custom && (
                                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400">
                                        O'zgartirilgan
                                    </span>
                                )}
                                {editingKey !== p.key ? (
                                    <button
                                        onClick={() => { setEditingKey(p.key); setEditValue(p.value); }}
                                        className="text-xs px-2 py-1 rounded-md bg-primary/20 text-primary hover:bg-primary/30"
                                    >
                                        ✏️ Tahrirlash
                                    </button>
                                ) : null}
                            </div>
                        </div>

                        {editingKey === p.key ? (
                            <div className="space-y-2">
                                <textarea
                                    className="w-full bg-secondary/50 border border-border/30 rounded-md p-2 text-sm min-h-[120px] font-mono"
                                    value={editValue}
                                    onChange={(e) => setEditValue(e.target.value)}
                                />
                                {p.key === "prompt_copywriter" && (
                                    <p className="text-[10px] text-muted-foreground">
                                        Mavjud o'zgaruvchilar: {"{copy_desc}"}, {"{prompt}"}, {"{copy_type}"}
                                    </p>
                                )}
                                {p.key === "prompt_imagegen" && (
                                    <p className="text-[10px] text-muted-foreground">
                                        Mavjud o'zgaruvchi: {"{prompt}"} — foydalanuvchi so'rovi
                                    </p>
                                )}
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => savePrompt(p.key)}
                                        disabled={saving}
                                        className="flex-1 py-2 bg-primary text-primary-foreground text-xs rounded-md hover:opacity-90 disabled:opacity-50"
                                    >
                                        {saving ? "Saqlanmoqda..." : "💾 Saqlash"}
                                    </button>
                                    {p.is_custom && (
                                        <button
                                            onClick={() => resetPrompt(p.key)}
                                            className="px-3 py-2 bg-red-500/20 text-red-400 text-xs rounded-md hover:bg-red-500/30"
                                        >
                                            🔄 Standart
                                        </button>
                                    )}
                                    <button
                                        onClick={() => setEditingKey(null)}
                                        className="px-3 py-2 bg-secondary text-muted-foreground text-xs rounded-md hover:bg-secondary/80"
                                    >
                                        ✕
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <pre className="text-xs text-muted-foreground whitespace-pre-wrap bg-secondary/30 rounded p-2 max-h-24 overflow-auto">
                                {p.value}
                            </pre>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
