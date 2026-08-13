import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { fetchApi } from "@/lib/api";

interface Application {
    id: number;
    user_name: string | null;
    telegram_id: number;
    answers: Record<string, string>;
    score: number;
    tier: string;
    created_at: string;
}

const TIER_LABELS: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
    cold: { label: "Sovuq", variant: "outline" },
    warm: { label: "Iliq", variant: "secondary" },
    hot: { label: "Issiq", variant: "default" },
    ready: { label: "Tayyor", variant: "default" },
};

export default function Applications() {
    const [tierFilter, setTierFilter] = useState<string>("all");

    const { data, isLoading } = useQuery<{ applications: Application[] }>({
        queryKey: ["crm-applications", tierFilter],
        queryFn: () => fetchApi(`/api/admin/crm/applications${tierFilter !== "all" ? `?tier=${tierFilter}` : ""}`),
    });

    const applications = data?.applications || [];

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">Arizalar</h2>
                <Select value={tierFilter} onValueChange={setTierFilter}>
                    <SelectTrigger className="w-[160px]">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">Barchasi</SelectItem>
                        <SelectItem value="ready">Tayyor</SelectItem>
                        <SelectItem value="hot">Issiq</SelectItem>
                        <SelectItem value="warm">Iliq</SelectItem>
                        <SelectItem value="cold">Sovuq</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {isLoading ? (
                <div className="flex justify-center p-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            ) : applications.length === 0 ? (
                <div className="text-center p-8 border rounded-lg border-dashed text-muted-foreground">
                    <p>Hozircha ariza yo'q.</p>
                </div>
            ) : (
                <div className="grid gap-3">
                    {applications.map((app) => {
                        const tier = TIER_LABELS[app.tier] || { label: app.tier, variant: "outline" as const };
                        return (
                            <div key={app.id} className="glass-card p-4 rounded-xl">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-semibold">{app.user_name || "Noma'lum"}</span>
                                    <Badge variant={tier.variant}>{tier.label} · {app.score} ball</Badge>
                                </div>
                                <p className="text-xs text-muted-foreground mb-2">
                                    ID: {app.telegram_id} · {app.created_at ? new Date(app.created_at).toLocaleString() : ""}
                                </p>
                                <div className="flex flex-wrap gap-1.5">
                                    {Object.entries(app.answers || {}).map(([k, v]) => (
                                        <Badge key={k} variant="outline" className="text-[10px]">{k}: {v}</Badge>
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
