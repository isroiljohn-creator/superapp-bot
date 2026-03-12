import { Card, CardContent } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

interface FunnelStep {
  label: string;
  users: number;
  rate: number;
}

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

  // Find worst drop-off
  let worstFrom = "—";
  let worstTo = "—";
  let worstCount = 0;
  for (let i = 1; i < steps.length; i++) {
    const drop = steps[i - 1].users - steps[i].users;
    if (drop > worstCount) {
      worstCount = drop;
      worstFrom = steps[i - 1].label;
      worstTo = steps[i].label;
    }
  }

  // Find best retention step
  let bestFrom = "—";
  let bestTo = "—";
  let bestRate = 0;
  for (let i = 1; i < steps.length; i++) {
    const rate = steps[i - 1].users > 0 ? (steps[i].users / steps[i - 1].users * 100) : 0;
    if (rate > bestRate) {
      bestRate = rate;
      bestFrom = steps[i - 1].label;
      bestTo = steps[i].label;
    }
  }

  return (
    <div className="space-y-3">
      {/* Funnel bars */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          {isLoading ? (
            <div className="text-xs text-muted-foreground text-center py-8">Yuklanmoqda…</div>
          ) : steps.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-8">Ma'lumot topilmadi</div>
          ) : (
            <div className="space-y-1.5">
              {steps.map((step, i) => {
                const pct = Math.max((step.users / maxUsers) * 100, 8);
                const colors = ["#38bdf8", "#22b8cf", "#20c997", "#51cf66", "#fcc419", "#ff922b", "#ff6b6b"];
                const color = colors[i % colors.length];
                const drop = i > 0 && steps[i - 1].users > 0
                  ? ((steps[i - 1].users - step.users) / steps[i - 1].users * 100).toFixed(0)
                  : null;

                return (
                  <div key={step.label} className="flex items-center gap-2" style={{ height: '32px' }}>
                    <span className="text-xs w-20 md:w-28 text-right truncate flex-shrink-0 text-muted-foreground">
                      {step.label}
                    </span>
                    <div className="flex-1 h-full relative">
                      <div
                        className="h-full rounded flex items-center transition-all duration-500"
                        style={{ width: `${pct}%`, backgroundColor: color, minWidth: '40px' }}
                      >
                        <span className="text-[10px] font-bold text-white px-1.5 drop-shadow whitespace-nowrap">
                          {step.users.toLocaleString()}
                        </span>
                      </div>
                    </div>
                    <span className="text-[10px] w-10 text-right flex-shrink-0 font-medium" style={{ color: drop && Number(drop) > 0 ? '#ff6b6b' : 'transparent' }}>
                      {drop && Number(drop) > 0 ? `−${drop}%` : ""}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Summary cards */}
      {!isLoading && steps.length >= 2 && (
        <div className="grid grid-cols-3 gap-2">
          {/* Konversiya */}
          <Card className="glass-card border-border/30">
            <CardContent className="p-2.5 text-center">
              <p className="text-xl font-bold text-primary leading-none">{totalConv}%</p>
              <p className="text-[10px] text-muted-foreground mt-1">Konversiya</p>
            </CardContent>
          </Card>

          {/* Eng katta yo'qotish */}
          <Card className="glass-card border-border/30">
            <CardContent className="p-2.5 text-center">
              <p className="text-xs font-bold text-destructive leading-tight truncate">{worstFrom}</p>
              <p className="text-[10px] text-destructive/60">↓</p>
              <p className="text-xs font-bold text-destructive leading-tight truncate">{worstTo}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">Yo'qotish</p>
            </CardContent>
          </Card>

          {/* Eng yaxshi bosqich */}
          <Card className="glass-card border-border/30">
            <CardContent className="p-2.5 text-center">
              <p className="text-xs font-bold text-success leading-tight truncate">{bestFrom}</p>
              <p className="text-[10px] text-success/60">↓</p>
              <p className="text-xs font-bold text-success leading-tight truncate">{bestTo}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">Yaxshi</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
