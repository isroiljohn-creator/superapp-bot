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
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-bold">🔻 Voronka analitikasi</h2>
      </div>

      {/* Funnel Visualization */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-4 md:p-6 space-y-1">
          {isLoading ? (
            <div className="text-xs text-muted-foreground text-center py-8">Yuklanmoqda...</div>
          ) : funnelSteps.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-8">Ma'lumot topilmadi</div>
          ) : (
            funnelSteps.map((step, i) => {
              const widthPct = Math.max((step.users / maxUsers) * 100, 8);
              const dropoff = i > 0
                ? (((funnelSteps[i - 1].users - step.users) / funnelSteps[i - 1].users) * 100).toFixed(0)
                : null;
              const color = stepColors[i % stepColors.length];

              return (
                <div key={step.label} className="group">
                  {/* Drop-off indicator between steps */}
                  {dropoff && Number(dropoff) > 0 && (
                    <div className="flex items-center justify-center py-0.5">
                      <span className="text-[10px] text-destructive/70 font-medium">
                        ↓ −{dropoff}% yo'qolgan ({funnelSteps[i - 1].users - step.users} ta)
                      </span>
                    </div>
                  )}
                  <motion.div
                    initial={{ width: 0, opacity: 0 }}
                    animate={{ width: "100%", opacity: 1 }}
                    transition={{ duration: 0.5, delay: i * 0.1 }}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-medium w-32 md:w-40 flex-shrink-0 truncate">{step.label}</span>
                      <div className="flex-1 relative">
                        <motion.div
                          className="h-9 md:h-10 rounded-lg flex items-center relative"
                          initial={{ width: 0 }}
                          animate={{ width: `${widthPct}%` }}
                          transition={{ duration: 0.8, delay: i * 0.12, ease: "easeOut" }}
                          style={{ background: color, minWidth: "60px" }}
                        >
                          <span className="absolute right-2 text-[11px] font-bold text-white drop-shadow">
                            {step.users.toLocaleString()}
                          </span>
                        </motion.div>
                      </div>
                      {i > 0 && (
                        <span className="text-[11px] font-semibold w-10 text-right flex-shrink-0" style={{ color }}>
                          {step.rate}%
                        </span>
                      )}
                    </div>
                  </motion.div>
                </div>
              );
            })
          )}
        </CardContent>
      </Card>

      {/* Summary — responsive grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Card className="glass-card border-border/30">
          <CardContent className="p-3 md:p-4">
            <p className="text-[10px] text-muted-foreground mb-1">Umumiy konversiya</p>
            <p className="text-2xl font-bold text-primary">{totalConversion}%</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">
              /start → To'lov
            </p>
          </CardContent>
        </Card>
        <Card className="glass-card border-border/30 border-destructive/20">
          <CardContent className="p-3 md:p-4">
            <p className="text-[10px] text-muted-foreground mb-1">🔴 Eng katta yo'qotish</p>
            <p className="text-sm font-bold text-destructive truncate">{biggestDropLabel}</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">
              {biggestDrop.toLocaleString()} ta foydalanuvchi
            </p>
          </CardContent>
        </Card>
        <Card className="glass-card border-border/30 border-success/20">
          <CardContent className="p-3 md:p-4">
            <p className="text-[10px] text-muted-foreground mb-1">🟢 Eng yaxshi bosqich</p>
            <p className="text-sm font-bold text-success truncate">{bestStepLabel}</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">
              {bestRate.toFixed(0)}% konversiya
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
