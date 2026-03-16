import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

interface DailyData {
  date: string;
  users: number;
}

interface FunnelStep {
  label: string;
  users: number;
  rate: number;
}

export default function AnalyticsCharts() {
  const { data: dailyData = [], isLoading: growthLoading } = useQuery<DailyData[]>({
    queryKey: ["admin_daily_growth"],
    queryFn: () => fetchApi("/api/admin/analytics/daily-growth"),
  });

  const { data: funnel = [], isLoading: funnelLoading } = useQuery<FunnelStep[]>({
    queryKey: ["admin_funnel_charts"],
    queryFn: () => fetchApi("/api/admin/funnel"),
  });

  const loading = growthLoading || funnelLoading;
  const maxUsers = Math.max(...dailyData.map((d) => d.users), 1);
  const maxFunnel = funnel.length > 0 ? funnel[0].users : 1;

  if (loading)
    return (
      <div className="text-center py-8 text-muted-foreground">
        Yuklanmoqda...
      </div>
    );

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-bold">📊 Analytics</h2>

      {/* Daily Growth Chart */}
      <div className="bg-card border border-border/30 rounded-lg p-4">
        <h3 className="text-sm font-semibold mb-3">
          📈 Kunlik o'sish (30 kun)
        </h3>
        {dailyData.length === 0 ? (
          <p className="text-xs text-muted-foreground">Ma'lumot yo'q</p>
        ) : (
          <div className="flex items-end gap-1 h-32">
            {dailyData.map((d, i) => {
              const height = Math.max(4, (d.users / maxUsers) * 100);
              return (
                <div
                  key={i}
                  className="flex-1 group relative"
                  title={`${d.date}: ${d.users} ta`}
                >
                  <div
                    className="bg-primary/70 hover:bg-primary rounded-t transition-all mx-[1px]"
                    style={{ height: `${height}%` }}
                  />
                  {/* Tooltip on hover */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 hidden group-hover:block bg-popover text-popover-foreground text-[9px] px-1.5 py-0.5 rounded shadow whitespace-nowrap mb-1 z-10">
                    {d.date.slice(5)}: {d.users}
                  </div>
                </div>
              );
            })}
          </div>
        )}
        <div className="flex justify-between text-[9px] text-muted-foreground mt-1">
          <span>{dailyData[0]?.date?.slice(5) || ""}</span>
          <span>{dailyData[dailyData.length - 1]?.date?.slice(5) || ""}</span>
        </div>
        <div className="text-right text-xs text-muted-foreground mt-1">
          Jami:{" "}
          <b>{dailyData.reduce((s, d) => s + d.users, 0)}</b> ta yangi
          foydalanuvchi
        </div>
      </div>

      {/* Funnel */}
      <div className="bg-card border border-border/30 rounded-lg p-4">
        <h3 className="text-sm font-semibold mb-3">🔄 Konversiya Funnel</h3>
        <div className="space-y-2">
          {funnel.map((stage, i) => {
            const width = Math.max(10, (stage.users / maxFunnel) * 100);
            const convRate =
              i > 0 && funnel[i - 1].users > 0
                ? ((stage.users / funnel[i - 1].users) * 100).toFixed(1)
                : null;
            return (
              <div key={i}>
                <div className="flex justify-between text-xs mb-0.5">
                  <span>{stage.label}</span>
                  <span className="font-medium">
                    {stage.users}
                    {convRate && (
                      <span className="text-muted-foreground ml-1">
                        ({convRate}%)
                      </span>
                    )}
                  </span>
                </div>
                <div className="h-6 bg-secondary/50 rounded overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary/80 to-primary rounded transition-all"
                    style={{ width: `${width}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
