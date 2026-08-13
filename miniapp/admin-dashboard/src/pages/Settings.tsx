import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

const SETTING_KEYS = [
    { key: "warmup_day_1", label: "Progrev 1-kun (tanishuv)", placeholder: "Kodda tayyor matn bor — bu yerda o'zgartirsangiz, o'sha ishlatiladi" },
    { key: "warmup_day_2", label: "Progrev 2-kun (talaba tajribasi)", placeholder: "Kodda tayyor matn bor — bu yerda o'zgartirsangiz, o'sha ishlatiladi" },
    { key: "warmup_day_3", label: "Progrev 3-kun (amaliy dars)", placeholder: "Kodda tayyor matn bor — bu yerda o'zgartirsangiz, o'sha ishlatiladi" },
    { key: "warmup_day_4", label: "Progrev 4-kun (keng tarqalgan xato)", placeholder: "Kodda tayyor matn bor — bu yerda o'zgartirsangiz, o'sha ishlatiladi" },
    { key: "warmup_day_5", label: "Progrev 5-kun (kulisa ortida)", placeholder: "Kodda tayyor matn bor — bu yerda o'zgartirsangiz, o'sha ishlatiladi" },
    { key: "warmup_day_6", label: "Progrev 6-kun (case breakdown)", placeholder: "Kodda tayyor matn bor — bu yerda o'zgartirsangiz, o'sha ishlatiladi" },
    { key: "warmup_day_7", label: "Progrev 7-kun (taklif)", placeholder: "Kodda tayyor matn bor — bu yerda o'zgartirsangiz, o'sha ishlatiladi" },
    { key: "warmup_day_1_media", label: "1-kun rasm/video file_id (ixtiyoriy)", placeholder: "Telegram file_id" },
    { key: "warmup_day_5_media", label: "5-kun rasm/video file_id (ixtiyoriy)", placeholder: "Telegram file_id" },
    { key: "warmup_day_6_media", label: "6-kun rasm/video file_id (ixtiyoriy)", placeholder: "Telegram file_id" },
    { key: "masterclass_video_file_id", label: "Masterclass video file_id", placeholder: "Telegram file_id (tripwire xariddan keyin yuboriladi)" },
    { key: "masterclass_delay_seconds", label: "Masterclass kechikishi (soniya)", placeholder: "3600" },
    { key: "churn_day_1", label: "Churn Day 1 (reminder)", placeholder: "Salom {name}! Sizni sog'indik..." },
    { key: "churn_day_3", label: "Churn Day 3 (value video)", placeholder: "{name}, sizga maxsus video tayyorladik..." },
    { key: "churn_day_5", label: "Churn Day 5 (discount)", placeholder: "{name}, 30% chegirma! Narx: {discounted_price}" },
    { key: "churn_day_7", label: "Churn Day 7 (farewell)", placeholder: "{name}, obunangiz tugadi..." },
    { key: "referral_reward", label: "Referal mukofoti (so'm)", placeholder: "500" },
    { key: "club_price", label: "Klub narxi (so'm)", placeholder: "97000" },
];

export default function Settings() {
    const { toast } = useToast();
    const [localSettings, setLocalSettings] = useState<Record<string, string>>({});

    const { isLoading } = useQuery<Record<string, string>>({
        queryKey: ["admin_settings"],
        queryFn: async () => {
            const data = await fetchApi("/api/admin/settings");
            const map: Record<string, string> = {};
            if (Array.isArray(data)) {
                data.forEach((s: any) => { map[s.key] = s.value; });
            } else {
                Object.assign(map, data);
            }
            setLocalSettings(map);
            return map;
        },
    });

    const saveMutation = useMutation({
        mutationFn: ({ key, value }: { key: string; value: string }) =>
            fetchApi(`/api/admin/settings/${key}`, {
                method: "PUT",
                body: JSON.stringify({ value }),
            }),
        onSuccess: (_, { key }) => {
            toast({ title: "Saqlandi", description: `${key} yangilandi` });
        },
        onError: (err: Error) => toast({ title: "Xatolik", description: err.message, variant: "destructive" }),
    });

    if (isLoading) return <div className="text-center py-8 text-muted-foreground">Yuklanmoqda...</div>;

    return (
        <div className="space-y-6">
            <h2 className="text-lg font-bold">Sozlamalar</h2>

            <div className="space-y-4">
                {SETTING_KEYS.map(({ key, label, placeholder }) => (
                    <div key={key} className="bg-card border border-border/30 rounded-lg p-4 space-y-2">
                        <label className="text-sm font-medium text-foreground">{label}</label>
                        {key.startsWith("churn_") || (key.startsWith("warmup_") && !key.includes("_media")) ? (
                            <textarea
                                className="w-full bg-secondary/50 border border-border/30 rounded-md p-2 text-sm min-h-[80px] resize-y"
                                placeholder={placeholder}
                                value={localSettings[key] || ""}
                                onChange={(e) => setLocalSettings(prev => ({ ...prev, [key]: e.target.value }))}
                            />
                        ) : (
                            <input
                                type="text"
                                className="w-full bg-secondary/50 border border-border/30 rounded-md p-2 text-sm"
                                placeholder={placeholder}
                                value={localSettings[key] || ""}
                                onChange={(e) => setLocalSettings(prev => ({ ...prev, [key]: e.target.value }))}
                            />
                        )}
                        <button
                            onClick={() => saveMutation.mutate({ key, value: localSettings[key] || "" })}
                            disabled={saveMutation.isPending && saveMutation.variables?.key === key}
                            className="px-3 py-1.5 bg-primary text-primary-foreground text-xs rounded-md hover:opacity-90 disabled:opacity-50"
                        >
                            {saveMutation.isPending && saveMutation.variables?.key === key ? "Saqlanmoqda..." : "Saqlash"}
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}
