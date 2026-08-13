import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, UserCog } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { fetchApi } from "@/lib/api";

interface Staff {
    id: number;
    username: string;
    role: string;
    is_active: boolean;
}

const ROLE_LABELS: Record<string, string> = {
    admin: "Admin",
    sales: "Sotuvchi",
    marketing: "Marketolog",
};

export default function StaffManager() {
    const queryClient = useQueryClient();
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [form, setForm] = useState({ username: "", password: "", role: "sales" });

    const { data, isLoading } = useQuery<{ staff: Staff[] }>({
        queryKey: ["crm-staff"],
        queryFn: () => fetchApi("/api/admin/crm/staff"),
    });

    const createMutation = useMutation({
        mutationFn: () => fetchApi("/api/admin/crm/staff", { method: "POST", body: JSON.stringify(form) }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["crm-staff"] });
            toast.success("Xodim qo'shildi");
            setIsDialogOpen(false);
            setForm({ username: "", password: "", role: "sales" });
        },
        onError: (e: Error) => toast.error(e.message),
    });

    const toggleActive = useMutation({
        mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
            fetchApi(`/api/admin/crm/staff/${id}`, { method: "PATCH", body: JSON.stringify({ is_active }) }),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["crm-staff"] }),
        onError: (e: Error) => toast.error(e.message),
    });

    const deleteMutation = useMutation({
        mutationFn: (id: number) => fetchApi(`/api/admin/crm/staff/${id}`, { method: "DELETE" }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["crm-staff"] });
            toast.success("Xodim o'chirildi");
        },
        onError: (e: Error) => toast.error(e.message),
    });

    const staff = data?.staff || [];

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">Xodimlar</h2>
                <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                    <DialogTrigger asChild>
                        <Button size="sm" className="gap-2">
                            <Plus className="h-4 w-4" /> Qo'shish
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[400px]">
                        <DialogHeader>
                            <DialogTitle>Yangi xodim</DialogTitle>
                        </DialogHeader>
                        <form
                            onSubmit={(e) => { e.preventDefault(); createMutation.mutate(); }}
                            className="space-y-4 pt-4"
                        >
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Username</label>
                                <Input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Parol</label>
                                <Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Rol</label>
                                <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
                                    <SelectTrigger><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="sales">Sotuvchi</SelectItem>
                                        <SelectItem value="marketing">Marketolog</SelectItem>
                                        <SelectItem value="admin">Admin</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                                Saqlash
                            </Button>
                        </form>
                    </DialogContent>
                </Dialog>
            </div>

            {isLoading ? (
                <div className="flex justify-center p-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            ) : (
                <div className="grid gap-3">
                    {staff.map((s) => (
                        <div key={s.id} className="glass-card p-4 rounded-xl flex items-center justify-between gap-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-primary/10 text-primary">
                                    <UserCog className="h-4 w-4" />
                                </div>
                                <div>
                                    <p className="font-semibold">{s.username}</p>
                                    <Badge variant="secondary">{ROLE_LABELS[s.role] || s.role}</Badge>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => toggleActive.mutate({ id: s.id, is_active: !s.is_active })}
                                >
                                    <span className={`h-1.5 w-1.5 rounded-full mr-1.5 inline-block ${s.is_active ? "bg-success" : "bg-muted-foreground"}`} />
                                    {s.is_active ? "Aktiv" : "O'chirilgan"}
                                </Button>
                                <Button
                                    size="icon"
                                    variant="destructive"
                                    onClick={() => { if (confirm("O'chirilsinmi?")) deleteMutation.mutate(s.id); }}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
