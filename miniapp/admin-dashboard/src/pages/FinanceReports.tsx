import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { fetchApi } from "@/lib/api";

interface FinanceSummary {
    total_revenue: number;
    total_expense: number;
    profit: number;
    by_product: { product_code: string; revenue: number; count: number }[];
    daily_revenue: { day: string; revenue: number }[];
}

interface Expense {
    id: number;
    category: string;
    amount: number;
    description: string | null;
    expense_date: string;
}

export default function FinanceReports() {
    const queryClient = useQueryClient();
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [form, setForm] = useState({ category: "ads", amount: "", description: "", expense_date: new Date().toISOString().slice(0, 10) });

    const { data: summary, isLoading } = useQuery<FinanceSummary>({
        queryKey: ["crm-finance-summary"],
        queryFn: () => fetchApi("/api/admin/crm/finance/summary"),
    });

    const { data: expensesData } = useQuery<{ expenses: Expense[] }>({
        queryKey: ["crm-expenses"],
        queryFn: () => fetchApi("/api/admin/crm/expenses"),
    });

    const createExpense = useMutation({
        mutationFn: () => fetchApi("/api/admin/crm/expenses", {
            method: "POST",
            body: JSON.stringify({ ...form, amount: Number(form.amount) }),
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["crm-expenses"] });
            queryClient.invalidateQueries({ queryKey: ["crm-finance-summary"] });
            toast.success("Xarajat qo'shildi");
            setIsDialogOpen(false);
            setForm({ category: "ads", amount: "", description: "", expense_date: new Date().toISOString().slice(0, 10) });
        },
        onError: (e: Error) => toast.error(e.message),
    });

    const deleteExpense = useMutation({
        mutationFn: (id: number) => fetchApi(`/api/admin/crm/expenses/${id}`, { method: "DELETE" }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["crm-expenses"] });
            queryClient.invalidateQueries({ queryKey: ["crm-finance-summary"] });
        },
        onError: (e: Error) => toast.error(e.message),
    });

    if (isLoading || !summary) {
        return (
            <div className="flex justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    const expenses = expensesData?.expenses || [];

    return (
        <div className="space-y-4">
            <h2 className="text-xl font-bold">Moliyaviy hisobot</h2>

            <div className="grid grid-cols-3 gap-3">
                <div className="glass-card p-4 rounded-xl">
                    <p className="text-xs text-muted-foreground">Daromad</p>
                    <p className="text-lg font-bold text-green-500">{summary.total_revenue.toLocaleString()}</p>
                </div>
                <div className="glass-card p-4 rounded-xl">
                    <p className="text-xs text-muted-foreground">Xarajat</p>
                    <p className="text-lg font-bold text-red-500">{summary.total_expense.toLocaleString()}</p>
                </div>
                <div className="glass-card p-4 rounded-xl">
                    <p className="text-xs text-muted-foreground">Foyda</p>
                    <p className={`text-lg font-bold ${summary.profit >= 0 ? "text-green-500" : "text-red-500"}`}>
                        {summary.profit.toLocaleString()}
                    </p>
                </div>
            </div>

            <div className="glass-card p-4 rounded-xl h-64">
                <p className="text-sm font-semibold mb-2">Kunlik daromad</p>
                <ResponsiveContainer width="100%" height="90%">
                    <BarChart data={summary.daily_revenue} margin={{ top: 4, right: 4, left: -10, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                        <XAxis dataKey="day" fontSize={10} />
                        <YAxis fontSize={10} />
                        <Tooltip />
                        <Bar dataKey="revenue" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            <div className="grid gap-2">
                <p className="text-sm font-semibold">Mahsulot bo'yicha daromad</p>
                {summary.by_product.map((p) => (
                    <div key={p.product_code} className="glass-card p-3 rounded-lg flex justify-between text-sm">
                        <span>{p.product_code} ({p.count} ta)</span>
                        <span className="font-semibold">{p.revenue.toLocaleString()} so'm</span>
                    </div>
                ))}
            </div>

            <div className="flex items-center justify-between pt-2">
                <p className="text-sm font-semibold">Xarajatlar</p>
                <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                    <DialogTrigger asChild>
                        <Button size="sm" className="gap-2"><Plus className="h-4 w-4" /> Xarajat qo'shish</Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[400px]">
                        <DialogHeader><DialogTitle>Yangi xarajat</DialogTitle></DialogHeader>
                        <form onSubmit={(e) => { e.preventDefault(); createExpense.mutate(); }} className="space-y-4 pt-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Kategoriya</label>
                                <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                                    <SelectTrigger><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="ads">Reklama</SelectItem>
                                        <SelectItem value="salary">Maosh</SelectItem>
                                        <SelectItem value="tools">Vositalar</SelectItem>
                                        <SelectItem value="other">Boshqa</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Summa (so'm)</label>
                                <Input type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Sana</label>
                                <Input type="date" value={form.expense_date} onChange={(e) => setForm({ ...form, expense_date: e.target.value })} required />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Izoh</label>
                                <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                            </div>
                            <Button type="submit" className="w-full" disabled={createExpense.isPending}>Saqlash</Button>
                        </form>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="grid gap-2">
                {expenses.map((e) => (
                    <div key={e.id} className="glass-card p-3 rounded-lg flex items-center justify-between text-sm">
                        <div>
                            <p className="font-medium">{e.category} — {e.amount.toLocaleString()} so'm</p>
                            <p className="text-xs text-muted-foreground">{e.expense_date?.slice(0, 10)} {e.description ? `· ${e.description}` : ""}</p>
                        </div>
                        <Button size="icon" variant="ghost" onClick={() => deleteExpense.mutate(e.id)}>
                            <Trash2 className="h-4 w-4" />
                        </Button>
                    </div>
                ))}
            </div>
        </div>
    );
}
