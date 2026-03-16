import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface Prompt {
    key: string;
    label: string;
    value: string;
    is_custom: boolean;
    default: string;
}

export default function PromptManager() {
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const [editingKey, setEditingKey] = useState<string | null>(null);
    const [editValue, setEditValue] = useState("");

    const { data: prompts = [], isLoading } = useQuery<Prompt[]>({
        queryKey: ["admin_prompts"],
        queryFn: () => fetchApi("/api/admin/prompts"),
    });

    const saveMutation = useMutation({
        mutationFn: ({ key, value }: { key: string; value: string }) =>
            fetchApi("/api/admin/prompts", {
                method: "PUT",
                body: JSON.stringify({ key, value }),
            }),
        onSuccess: () => {
            toast({ title: "✅ Prompt saqlandi" });
            setEditingKey(null);
            queryClient.invalidateQueries({ queryKey: ["admin_prompts"] });
        },
        onError: (err: Error) => toast({ title: "Xatolik", description: err.message, variant: "destructive" }),
    });

    const resetMutation = useMutation({
        mutationFn: (key: string) =>
            fetchApi(`/api/admin/prompts/${key}`, { method: "DELETE" }),
        onSuccess: () => {
            toast({ title: "🔄 Standart qiymatga qaytarildi" });
            setEditingKey(null);
            queryClient.invalidateQueries({ queryKey: ["admin_prompts"] });
        },
        onError: (err: Error) => toast({ title: "Xatolik", description: err.message, variant: "destructive" }),
    });

    if (isLoading) return <div className="text-center py-8 text-muted-foreground">Yuklanmoqda...</div>;

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
                                        onClick={() => saveMutation.mutate({ key: p.key, value: editValue })}
                                        disabled={saveMutation.isPending}
                                        className="flex-1 py-2 bg-primary text-primary-foreground text-xs rounded-md hover:opacity-90 disabled:opacity-50"
                                    >
                                        {saveMutation.isPending ? "Saqlanmoqda..." : "💾 Saqlash"}
                                    </button>
                                    {p.is_custom && (
                                        <button
                                            onClick={() => resetMutation.mutate(p.key)}
                                            disabled={resetMutation.isPending}
                                            className="px-3 py-2 bg-red-500/20 text-red-400 text-xs rounded-md hover:bg-red-500/30 disabled:opacity-50"
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
