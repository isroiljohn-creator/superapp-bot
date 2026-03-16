import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

interface DailyData {
  date: string;
  users: number;
  total: number;
}

interface FunnelStep {
  label: string;
  users: number;
  rate: number;
}

const PERIODS = [
  { label: "7 kun", days: 7 },
  { label: "30 kun", days: 30 },
  { label: "90 kun", days: 90 },
  { label: "Barchasi", days: 365 },
];

export default function AnalyticsCharts() {
  const [selectedDays, setSelectedDays] = useState(30);

  const { data: dailyData = [], isLoading: growthLoading } = useQuery<DailyData[]>({
    queryKey: ["admin_daily_growth", selectedDays],
    queryFn: () => fetchApi(`/api/admin/analytics/daily-growth?days=${selectedDays}`),
  });

  const { data: funnel = [], isLoading: funnelLoading } = useQuery<FunnelStep[]>({
    queryKey: ["admin_funnel_charts"],
    queryFn: () => fetchApi("/api/admin/funnel"),
  });

  const loading = growthLoading || funnelLoading;
  const maxTotal = Math.max(...dailyData.map((d) => d.total), 1);
  const minTotal = dailyData.length > 0 ? Math.min(...dailyData.map((d) => d.total)) : 0;
  const range = maxTotal - minTotal || 1;
  const maxFunnel = funnel.length > 0 ? funnel[0].users : 1;
  const totalNew = dailyData.reduce((s, d) => s + d.users, 0);
  const lastTotal = dailyData.length > 0 ? dailyData[dailyData.length - 1].total : 0;

  if (loading)
    return (
      <div className="text-center py-8 text-muted-foreground">
        Yuklanmoqda...
      </div>
    );

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-bold">📊 Tahlil</h2>

      {/* Daily Growth Chart with date selector */}
      <div className="bg-card border border-border/30 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold">
            📈 Foydalanuvchilar o'sishi
          </h3>
          <div className="flex gap-1">
            {PERIODS.map((p) => (
              <button
                key={p.days}
                onClick={() => setSelectedDays(p.days)}
                className={`text-[10px] px-2 py-0.5 rounded-full font-medium transition-colors ${
                  selectedDays === p.days
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-muted-foreground hover:bg-secondary/80"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {dailyData.length === 0 ? (
          <p className="text-xs text-muted-foreground">Ma'lumot yo'q</p>
        ) : (
          <div className="flex items-end gap-[2px] h-36">
            {dailyData.map((d, i) => {
              const height = Math.max(4, ((d.total - minTotal) / range) * 100);
              return (
                <div
                  key={i}
                  className="flex-1 group relative"
                  title={`${d.date}: Jami ${d.total.toLocaleString()}, Yangi +${d.users}`}
                >
                  <div
                    className="bg-primary/70 hover:bg-primary rounded-t transition-all"
                    style={{ height: `${height}%` }}
                  />
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 hidden group-hover:block bg-popover text-popover-foreground text-[9px] px-1.5 py-0.5 rounded shadow whitespace-nowrap mb-1 z-10">
                    {d.date.slice(5)}: {d.total.toLocaleString()} (+{d.users})
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
        <div className="flex justify-between text-xs text-muted-foreground mt-1.5">
          <span>
            Yangi: <b className="text-foreground">+{totalNew.toLocaleString()}</b> ta
          </span>
          <span>
            Jami: <b className="text-foreground">{lastTotal.toLocaleString()}</b> ta
          </span>
        </div>
      </div>

      {/* Funnel */}
      <div className="bg-card border border-border/30 rounded-lg p-4">
        <h3 className="text-sm font-semibold mb-3">🔄 Konversiya Funnel</h3>
        {funnel.length === 0 ? (
          <p className="text-xs text-muted-foreground">Ma'lumot yo'q</p>
        ) : (
          <div className="space-y-2">
            {funnel.map((stage, i) => {
              const width = Math.max(10, (stage.users / maxFunnel) * 100);
              return (
                <div key={i}>
                  <div className="flex justify-between text-xs mb-0.5">
                    <span>{stage.label}</span>
                    <span className="font-medium">
                      {stage.users.toLocaleString()}
                      <span className="text-muted-foreground ml-1">
                        ({stage.rate}%)
                      </span>
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
        )}
      </div>
    </div>
  );
}
