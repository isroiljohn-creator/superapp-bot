import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface ScheduledMsg {
    id: number;
    content: string;
    send_at: string;
    status: string;
    sent_count: number;
    created_at: string;
}

export default function ScheduledMessages() {
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const [showCreate, setShowCreate] = useState(false);
    const [content, setContent] = useState("");
    const [sendAt, setSendAt] = useState("");

    const { data: messages = [], isLoading } = useQuery<ScheduledMsg[]>({
        queryKey: ["admin_scheduled_messages"],
        queryFn: () => fetchApi("/api/admin/scheduled-messages"),
        refetchInterval: 10_000,
    });

    const createMutation = useMutation({
        mutationFn: () =>
            fetchApi("/api/admin/scheduled-messages", {
                method: "POST",
                body: JSON.stringify({ content, send_at: new Date(sendAt).toISOString() }),
            }),
        onSuccess: () => {
            toast({ title: "✅ Xabar rejalashtirildi" });
            setShowCreate(false);
            setContent("");
            setSendAt("");
            queryClient.invalidateQueries({ queryKey: ["admin_scheduled_messages"] });
        },
        onError: (err: Error) => toast({ title: "Xatolik", description: err.message, variant: "destructive" }),
    });

    const cancelMutation = useMutation({
        mutationFn: (id: number) =>
            fetchApi(`/api/admin/scheduled-messages/${id}`, { method: "DELETE" }),
        onSuccess: () => {
            toast({ title: "❌ Bekor qilindi" });
            queryClient.invalidateQueries({ queryKey: ["admin_scheduled_messages"] });
        },
        onError: (err: Error) => toast({ title: "Xatolik", description: err.message, variant: "destructive" }),
    });

    const statusBadge = (status: string) => {
        const colors: Record<string, string> = {
            pending: "bg-yellow-500/20 text-yellow-400",
            sent: "bg-green-500/20 text-green-400",
            cancelled: "bg-red-500/20 text-red-400",
            sending: "bg-blue-500/20 text-blue-400",
        };
        const labels: Record<string, string> = {
            pending: "⏳ Kutilmoqda",
            sent: "✅ Yuborilgan",
            cancelled: "❌ Bekor",
            sending: "📤 Yuborilmoqda",
        };
        return (
            <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${colors[status] || ""}`}>
                {labels[status] || status}
            </span>
        );
    };

    if (isLoading) return <div className="text-center py-8 text-muted-foreground">Yuklanmoqda...</div>;

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold">🔔 Rejali Xabarlar</h2>
                <button
                    onClick={() => setShowCreate(!showCreate)}
                    className="px-3 py-1.5 bg-primary text-primary-foreground text-xs rounded-md hover:opacity-90"
                >
                    {showCreate ? "✕ Yopish" : "+ Yangi xabar"}
                </button>
            </div>

            {showCreate && (
                <div className="bg-card border border-border/30 rounded-lg p-4 space-y-3">
                    <textarea
                        placeholder="Xabar matni (HTML qo'llab-quvvatlanadi)"
                        className="w-full bg-secondary/50 border border-border/30 rounded-md p-2 text-sm min-h-[80px]"
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                    />
                    <div>
                        <label className="text-xs text-muted-foreground">Yuborish vaqti</label>
                        <input
                            type="datetime-local"
                            className="w-full bg-secondary/50 border border-border/30 rounded-md p-2 text-sm"
                            value={sendAt}
                            onChange={(e) => setSendAt(e.target.value)}
                        />
                    </div>
                    <button
                        onClick={() => createMutation.mutate()}
                        disabled={!content.trim() || !sendAt || createMutation.isPending}
                        className="w-full py-2 bg-primary text-primary-foreground text-sm rounded-md hover:opacity-90 disabled:opacity-50"
                    >
                        {createMutation.isPending ? "Saqlanmoqda..." : "📅 Rejalash"}
                    </button>
                </div>
            )}

            {messages.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground text-sm">
                    Hali rejali xabarlar yo'q.
                </div>
            ) : (
                <div className="space-y-3">
                    {messages.map((msg) => (
                        <div key={msg.id} className="bg-card border border-border/30 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    {statusBadge(msg.status)}
                                    <span className="text-xs text-muted-foreground">
                                        {new Date(msg.send_at).toLocaleString("uz-UZ")}
                                    </span>
                                </div>
                                {msg.status === "pending" && (
                                    <button
                                        onClick={() => cancelMutation.mutate(msg.id)}
                                        disabled={cancelMutation.isPending}
                                        className="text-xs px-2 py-1 rounded-md bg-red-500/20 text-red-400 hover:bg-red-500/30 disabled:opacity-50"
                                    >
                                        ❌ Bekor
                                    </button>
                                )}
                            </div>
                            <p className="text-sm">{msg.content}</p>
                            {msg.sent_count > 0 && (
                                <p className="text-xs text-muted-foreground mt-1">
                                    📤 {msg.sent_count} ta yuborildi
                                </p>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
