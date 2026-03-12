import { Card, CardContent } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

interface FunnelStep {
  label: string;
  users: number;
  rate: number;
}

const stepColors = [
  "#38bdf8", "#22b8cf", "#20c997", "#51cf66",
  "#fcc419", "#ff922b", "#ff6b6b",
];

export default function FunnelAnalytics() {
  const { data: funnelData, isLoading } = useQuery<FunnelStep[]>({
    queryKey: ["admin_funnel"],
    queryFn: () => fetchApi("/api/admin/funnel"),
  });

  const steps = funnelData || [];
  const maxUsers = steps.length > 0 ? steps[0].users : 1;

  const totalConv = steps.length >= 2
    ? ((steps[steps.length - 1].users / steps[0].users) * 100).toFixed(1)
    : "0";

  let worstDrop = { label: "—", count: 0, pct: "0" };
  let bestStep = { label: "—", pct: 0 };

  for (let i = 1; i < steps.length; i++) {
    const drop = steps[i - 1].users - steps[i].users;
    const dropPct = steps[i - 1].users > 0 ? (drop / steps[i - 1].users * 100) : 0;
    if (drop > worstDrop.count) {
      worstDrop = { label: `${steps[i - 1].label} → ${steps[i].label}`, count: drop, pct: dropPct.toFixed(0) };
    }
    const rate = steps[i - 1].users > 0 ? (steps[i].users / steps[i - 1].users * 100) : 0;
    if (rate > bestStep.pct) {
      bestStep = { label: `${steps[i - 1].label} → ${steps[i].label}`, pct: rate };
    }
  }

  return (
    <div className="space-y-2.5">
      {/* Funnel bars */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-2.5">
          {isLoading ? (
            <div className="text-[11px] text-muted-foreground text-center py-6">Yuklanmoqda…</div>
          ) : steps.length === 0 ? (
            <div className="text-[11px] text-muted-foreground text-center py-6">Ma'lumot topilmadi</div>
          ) : (
            <div className="space-y-1">
              {steps.map((step, i) => {
                const pct = Math.max((step.users / maxUsers) * 100, 6);
                const color = stepColors[i % stepColors.length];
                const drop = i > 0 ? (((steps[i - 1].users - step.users) / steps[i - 1].users) * 100).toFixed(0) : null;

                return (
                  <div key={step.label} className="flex items-center gap-1.5" style={{ height: '28px' }}>
                    <span className="text-[9px] text-muted-foreground w-[72px] md:w-28 text-right truncate flex-shrink-0">
                      {step.label}
                    </span>
                    <div className="flex-1 h-full relative">
                      <div
                        className="h-full rounded-sm flex items-center transition-all duration-500"
                        style={{ width: `${pct}%`, backgroundColor: color, minWidth: '32px' }}
                      >
                        <span className="text-[9px] font-bold text-white px-1 drop-shadow whitespace-nowrap">
                          {step.users.toLocaleString()}
                        </span>
                      </div>
                    </div>
                    <span className="text-[9px] w-8 text-right flex-shrink-0" style={{ color: drop && Number(drop) > 0 ? '#ff6b6b' : 'transparent' }}>
                      {drop && Number(drop) > 0 ? `−${drop}%` : ""}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Summary row */}
      <div className="grid grid-cols-3 gap-1.5">
        <Card className="glass-card border-border/30">
          <CardContent className="p-2 text-center">
            <p className="text-lg font-bold text-primary leading-none">{totalConv}%</p>
            <p className="text-[8px] text-muted-foreground mt-0.5">Konversiya</p>
          </CardContent>
        </Card>
        <Card className="glass-card border-border/30">
          <CardContent className="p-2 text-center">
            <p className="text-[10px] font-bold text-destructive leading-tight truncate">{worstDrop.label}</p>
            <p className="text-[8px] text-muted-foreground mt-0.5">Katta yo'qotish</p>
          </CardContent>
        </Card>
        <Card className="glass-card border-border/30">
          <CardContent className="p-2 text-center">
            <p className="text-[10px] font-bold text-success leading-tight truncate">{bestStep.label}</p>
            <p className="text-[8px] text-muted-foreground mt-0.5">Yaxshi bosqich</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
