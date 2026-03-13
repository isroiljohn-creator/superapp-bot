import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";

const API_BASE = import.meta.env.VITE_API_URL || "";

function getAuthHeaders(): Record<string, string> {
    const initData = (window as any).Telegram?.WebApp?.initData || "";
    return initData ? { "Authorization": `tma ${initData}` } : {};
}

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
    const [messages, setMessages] = useState<ScheduledMsg[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [content, setContent] = useState("");
    const [sendAt, setSendAt] = useState("");

    useEffect(() => { fetchMessages(); }, []);

    const fetchMessages = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/admin/scheduled-messages`, {
                headers: getAuthHeaders(),
            });
            if (res.ok) setMessages(await res.json());
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    const createMessage = async () => {
        if (!content.trim() || !sendAt) return;
        try {
            const res = await fetch(`${API_BASE}/api/admin/scheduled-messages`, {
                method: "POST",
                headers: { "Content-Type": "application/json", ...getAuthHeaders() },
                body: JSON.stringify({ content, send_at: new Date(sendAt).toISOString() }),
            });
            if (res.ok) {
                toast({ title: "✅ Xabar rejalashtirildi" });
                setShowCreate(false);
                setContent("");
                setSendAt("");
                fetchMessages();
            }
        } catch (e) { console.error(e); }
    };

    const cancelMessage = async (id: number) => {
        try {
            const res = await fetch(`${API_BASE}/api/admin/scheduled-messages/${id}`, {
                method: "DELETE",
                headers: getAuthHeaders(),
            });
            if (res.ok) {
                toast({ title: "❌ Bekor qilindi" });
                fetchMessages();
            }
        } catch (e) { console.error(e); }
    };

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

    if (loading) return <div className="text-center py-8 text-muted-foreground">Yuklanmoqda...</div>;

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
                        onClick={createMessage}
                        className="w-full py-2 bg-primary text-primary-foreground text-sm rounded-md hover:opacity-90"
                    >
                        📅 Rejalash
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
                                        onClick={() => cancelMessage(msg.id)}
                                        className="text-xs px-2 py-1 rounded-md bg-red-500/20 text-red-400 hover:bg-red-500/30"
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
