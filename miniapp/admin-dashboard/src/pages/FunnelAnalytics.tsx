import { Card, CardContent } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import { motion } from "framer-motion";

interface FunnelStep {
  label: string;
  users: number;
  rate: number;
}

const stepColors = [
  "hsl(199, 85%, 55%)",
  "hsl(199, 75%, 50%)",
  "hsl(180, 60%, 45%)",
  "hsl(142, 60%, 45%)",
  "hsl(38, 80%, 50%)",
  "hsl(25, 85%, 55%)",
  "hsl(0, 72%, 55%)",
];

export default function FunnelAnalytics() {
  const { data: funnelData, isLoading } = useQuery<FunnelStep[]>({
    queryKey: ["admin_funnel"],
    queryFn: () => fetchApi("/api/admin/funnel"),
  });

  const funnelSteps = funnelData || [];
  const maxUsers = funnelSteps.length > 0 ? funnelSteps[0].users : 1;

  const totalConversion = funnelSteps.length >= 2
    ? ((funnelSteps[funnelSteps.length - 1].users / funnelSteps[0].users) * 100).toFixed(1)
    : "0";

  let biggestDropLabel = "—";
  let biggestDrop = 0;
  for (let i = 1; i < funnelSteps.length; i++) {
    const drop = funnelSteps[i - 1].users - funnelSteps[i].users;
    if (drop > biggestDrop) {
      biggestDrop = drop;
      biggestDropLabel = `${funnelSteps[i - 1].label} → ${funnelSteps[i].label}`;
    }
  }

  let bestStepLabel = "—";
  let bestRate = 0;
  for (let i = 1; i < funnelSteps.length; i++) {
    const rate = funnelSteps[i - 1].users > 0
      ? (funnelSteps[i].users / funnelSteps[i - 1].users) * 100
      : 0;
    if (rate > bestRate) {
      bestRate = rate;
      bestStepLabel = `${funnelSteps[i - 1].label} → ${funnelSteps[i].label}`;
    }
  }

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-bold">Voronka analitikasi</h2>

      {/* Funnel bars */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3 space-y-0.5">
          {isLoading ? (
            <div className="text-[11px] text-muted-foreground text-center py-6">Yuklanmoqda…</div>
          ) : funnelSteps.length === 0 ? (
            <div className="text-[11px] text-muted-foreground text-center py-6">Ma'lumot topilmadi</div>
          ) : (
            funnelSteps.map((step, i) => {
              const widthPct = Math.max((step.users / maxUsers) * 100, 10);
              const dropoff = i > 0
                ? (((funnelSteps[i - 1].users - step.users) / funnelSteps[i - 1].users) * 100).toFixed(0)
                : null;
              const color = stepColors[i % stepColors.length];

              return (
                <div key={step.label}>
                  {dropoff && Number(dropoff) > 0 && (
                    <div className="text-center py-px">
                      <span className="text-[9px] text-destructive/60">↓ −{dropoff}%</span>
                    </div>
                  )}
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-medium w-20 md:w-32 flex-shrink-0 truncate text-right">{step.label}</span>
                    <div className="flex-1 relative">
                      <motion.div
                        className="h-7 rounded-md flex items-center"
                        initial={{ width: 0 }}
                        animate={{ width: `${widthPct}%` }}
                        transition={{ duration: 0.6, delay: i * 0.1, ease: "easeOut" }}
                        style={{ background: color, minWidth: "40px" }}
                      >
                        <span className="absolute right-1.5 text-[10px] font-bold text-white drop-shadow">
                          {step.users.toLocaleString()}
                        </span>
                      </motion.div>
                    </div>
                    {i > 0 && (
                      <span className="text-[10px] font-semibold w-8 text-right flex-shrink-0" style={{ color }}>{step.rate}%</span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </CardContent>
      </Card>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-2">
        <Card className="glass-card border-border/30">
          <CardContent className="p-2 text-center">
            <p className="text-lg md:text-2xl font-bold text-primary">{totalConversion}%</p>
            <p className="text-[9px] text-muted-foreground">Konversiya</p>
          </CardContent>
        </Card>
        <Card className="glass-card border-border/30">
          <CardContent className="p-2 text-center">
            <p className="text-[11px] font-bold text-destructive truncate">{biggestDropLabel}</p>
            <p className="text-[9px] text-muted-foreground mt-0.5">Eng katta yo'qotish</p>
          </CardContent>
        </Card>
        <Card className="glass-card border-border/30">
          <CardContent className="p-2 text-center">
            <p className="text-[11px] font-bold text-success truncate">{bestStepLabel}</p>
            <p className="text-[9px] text-muted-foreground mt-0.5">Eng yaxshi</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
