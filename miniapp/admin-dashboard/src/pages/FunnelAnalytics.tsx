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

  return (
    <div className="space-y-3">
      {/* Conversion % header */}
      {!isLoading && steps.length >= 2 && (
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold text-primary">{totalConv}%</span>
          <span className="text-xs text-muted-foreground">umumiy konversiya</span>
        </div>
      )}

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
    </div>
  );
}
