import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Send, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { fetchApi } from "@/lib/api";

interface Deal {
    id: number;
    user_name: string | null;
    telegram_id: number;
    stage: string;
    amount: number | null;
}

interface Note {
    id: number;
    text: string;
    created_at: string;
}

interface DealTask {
    id: number;
    title: string;
    status: string;
    task_type: string;
    due_at: string | null;
}

export default function DealDetail({ deal, open, onClose }: { deal: Deal | null; open: boolean; onClose: () => void }) {
    const queryClient = useQueryClient();
    const [noteText, setNoteText] = useState("");
    const [taskTitle, setTaskTitle] = useState("");

    const { data: notesData } = useQuery({
        queryKey: ["deal-notes", deal?.id],
        queryFn: () => fetchApi(`/api/admin/crm/deals/${deal!.id}/notes`),
        enabled: !!deal,
    });

    const addNote = useMutation({
        mutationFn: (text: string) => fetchApi(`/api/admin/crm/deals/${deal!.id}/notes`, {
            method: "POST",
            body: JSON.stringify({ text }),
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["deal-notes", deal?.id] });
            setNoteText("");
            toast.success("Izoh qo'shildi");
        },
        onError: (e: Error) => toast.error(e.message),
    });

    const addTask = useMutation({
        mutationFn: (title: string) => fetchApi(`/api/admin/crm/deals/${deal!.id}/tasks`, {
            method: "POST",
            body: JSON.stringify({ title, task_type: "task" }),
        }),
        onSuccess: () => {
            setTaskTitle("");
            toast.success("Vazifa qo'shildi");
        },
        onError: (e: Error) => toast.error(e.message),
    });

    const sendInvoice = useMutation({
        mutationFn: () => fetchApi(`/api/admin/crm/deals/${deal!.id}/send_invoice`, { method: "POST" }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["crm-deals"] });
            toast.success("Invoice yuborildi");
        },
        onError: (e: Error) => toast.error(e.message),
    });

    if (!deal) return null;
    const notes: Note[] = notesData?.notes || [];

    return (
        <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
            <SheetContent className="w-full sm:max-w-md overflow-y-auto">
                <SheetHeader>
                    <SheetTitle className="flex items-center gap-2">
                        {deal.user_name || "Noma'lum"}
                        <Badge variant="secondary">{deal.stage}</Badge>
                    </SheetTitle>
                </SheetHeader>

                <div className="space-y-6 mt-4">
                    <div className="text-sm text-muted-foreground">
                        <p>Telegram ID: <code>{deal.telegram_id}</code></p>
                        {deal.amount && <p>Summa: {deal.amount.toLocaleString()} so'm</p>}
                    </div>

                    <Button
                        className="w-full gap-2"
                        onClick={() => sendInvoice.mutate()}
                        disabled={sendInvoice.isPending}
                    >
                        <Send className="h-4 w-4" /> To'liq kurs invoice yuborish
                    </Button>

                    <div className="space-y-2">
                        <h4 className="text-sm font-semibold flex items-center gap-2">
                            <CheckCircle2 className="h-4 w-4" /> Vazifa qo'shish
                        </h4>
                        <div className="flex gap-2">
                            <Input value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)} placeholder="Masalan: Ertaga qo'ng'iroq qilish" />
                            <Button
                                variant="secondary"
                                disabled={!taskTitle.trim() || addTask.isPending}
                                onClick={() => addTask.mutate(taskTitle)}
                            >
                                +
                            </Button>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <h4 className="text-sm font-semibold">Izohlar</h4>
                        <Textarea value={noteText} onChange={(e) => setNoteText(e.target.value)} placeholder="Izoh yozing..." rows={2} />
                        <Button
                            size="sm"
                            disabled={!noteText.trim() || addNote.isPending}
                            onClick={() => addNote.mutate(noteText)}
                        >
                            Saqlash
                        </Button>

                        <div className="space-y-2 pt-2">
                            {notes.map((n) => (
                                <div key={n.id} className="glass-card p-3 rounded-lg text-sm">
                                    <p>{n.text}</p>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        {n.created_at ? new Date(n.created_at).toLocaleString() : ""}
                                    </p>
                                </div>
                            ))}
                            {notes.length === 0 && (
                                <p className="text-xs text-muted-foreground">Hali izoh yo'q.</p>
                            )}
                        </div>
                    </div>
                </div>
            </SheetContent>
        </Sheet>
    );
}
