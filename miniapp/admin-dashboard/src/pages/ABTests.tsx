import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface ABTest {
    id: number;
    name: string;
    description: string;
    variant_a_name: string;
    variant_b_name: string;
    variant_a_value: string;
    variant_b_value: string;
    is_active: boolean;
    created_at: string;
}

export default function ABTests() {
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const [showCreate, setShowCreate] = useState(false);
    const [form, setForm] = useState({
        name: "", description: "",
        variant_a_name: "A", variant_b_name: "B",
        variant_a_value: "", variant_b_value: "",
    });

    const { data: tests = [], isLoading } = useQuery<ABTest[]>({
        queryKey: ["admin_ab_tests"],
        queryFn: () => fetchApi("/api/admin/ab-tests"),
    });

    const createMutation = useMutation({
        mutationFn: () =>
            fetchApi("/api/admin/ab-tests", {
                method: "POST",
                body: JSON.stringify(form),
            }),
        onSuccess: () => {
            toast({ title: "✅ Test yaratildi" });
            setShowCreate(false);
            setForm({ name: "", description: "", variant_a_name: "A", variant_b_name: "B", variant_a_value: "", variant_b_value: "" });
            queryClient.invalidateQueries({ queryKey: ["admin_ab_tests"] });
        },
        onError: (err: Error) => toast({ title: "Xatolik", description: err.message, variant: "destructive" }),
    });

    const toggleMutation = useMutation({
        mutationFn: (id: number) =>
            fetchApi(`/api/admin/ab-tests/${id}/toggle`, { method: "POST" }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin_ab_tests"] });
        },
        onError: (err: Error) => toast({ title: "Xatolik", description: err.message, variant: "destructive" }),
    });

    if (isLoading) return <div className="text-center py-8 text-muted-foreground">Yuklanmoqda...</div>;

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold">🎯 A/B Testlar</h2>
                <button
                    onClick={() => setShowCreate(!showCreate)}
                    className="px-3 py-1.5 bg-primary text-primary-foreground text-xs rounded-md hover:opacity-90"
                >
                    {showCreate ? "✕ Yopish" : "+ Yangi test"}
                </button>
            </div>

            {showCreate && (
                <div className="bg-card border border-border/30 rounded-lg p-4 space-y-3">
                    <input
                        type="text"
                        placeholder="Test nomi (masalan: welcome_message)"
                        className="w-full bg-secondary/50 border border-border/30 rounded-md p-2 text-sm"
                        value={form.name}
                        onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))}
                    />
                    <input
                        type="text"
                        placeholder="Tavsif"
                        className="w-full bg-secondary/50 border border-border/30 rounded-md p-2 text-sm"
                        value={form.description}
                        onChange={(e) => setForm(f => ({ ...f, description: e.target.value }))}
                    />
                    <div className="grid grid-cols-2 gap-2">
                        <div>
                            <label className="text-xs text-muted-foreground">Variant A nomi</label>
                            <input
                                type="text"
                                className="w-full bg-secondary/50 border border-border/30 rounded-md p-2 text-sm"
                                value={form.variant_a_name}
                                onChange={(e) => setForm(f => ({ ...f, variant_a_name: e.target.value }))}
                            />
                        </div>
                        <div>
                            <label className="text-xs text-muted-foreground">Variant B nomi</label>
                            <input
                                type="text"
                                className="w-full bg-secondary/50 border border-border/30 rounded-md p-2 text-sm"
                                value={form.variant_b_name}
                                onChange={(e) => setForm(f => ({ ...f, variant_b_name: e.target.value }))}
                            />
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                        <textarea
                            placeholder="Variant A matni"
                            className="bg-secondary/50 border border-border/30 rounded-md p-2 text-sm min-h-[60px]"
                            value={form.variant_a_value}
                            onChange={(e) => setForm(f => ({ ...f, variant_a_value: e.target.value }))}
                        />
                        <textarea
                            placeholder="Variant B matni"
                            className="bg-secondary/50 border border-border/30 rounded-md p-2 text-sm min-h-[60px]"
                            value={form.variant_b_value}
                            onChange={(e) => setForm(f => ({ ...f, variant_b_value: e.target.value }))}
                        />
                    </div>
                    <button
                        onClick={() => createMutation.mutate()}
                        disabled={!form.name.trim() || createMutation.isPending}
                        className="w-full py-2 bg-primary text-primary-foreground text-sm rounded-md hover:opacity-90 disabled:opacity-50"
                    >
                        {createMutation.isPending ? "Yaratilmoqda..." : "✅ Yaratish"}
                    </button>
                </div>
            )}

            {tests.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground text-sm">
                    Hali testlar yo'q. Yangi test yarating!
                </div>
            ) : (
                <div className="space-y-3">
                    {tests.map((test) => (
                        <div key={test.id} className="bg-card border border-border/30 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                                <div>
                                    <span className="font-medium text-sm">{test.name}</span>
                                    <span className={`ml-2 text-[10px] px-1.5 py-0.5 rounded-full ${test.is_active ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}`}>
                                        {test.is_active ? "Faol" : "O'chirilgan"}
                                    </span>
                                </div>
                                <button
                                    onClick={() => toggleMutation.mutate(test.id)}
                                    disabled={toggleMutation.isPending}
                                    className="text-xs px-2 py-1 rounded-md bg-secondary hover:bg-secondary/80 disabled:opacity-50"
                                >
                                    {test.is_active ? "⏸ O'chirish" : "▶️ Yoqish"}
                                </button>
                            </div>
                            {test.description && (
                                <p className="text-xs text-muted-foreground mb-2">{test.description}</p>
                            )}
                            <div className="grid grid-cols-2 gap-2 text-xs">
                                <div className="bg-secondary/40 p-2 rounded">
                                    <span className="font-medium">{test.variant_a_name}:</span> {test.variant_a_value || "—"}
                                </div>
                                <div className="bg-secondary/40 p-2 rounded">
                                    <span className="font-medium">{test.variant_b_name}:</span> {test.variant_b_value || "—"}
                                </div>
                            </div>
                            <div className="text-[10px] text-muted-foreground mt-2">
                                Yaratilgan: {test.created_at}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
