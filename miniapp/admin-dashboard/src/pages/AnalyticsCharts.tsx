import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

interface FunnelStep {
  label: string;
  users: number;
  rate: number;
}

export default function AnalyticsCharts() {
  const { data: funnel = [], isLoading } = useQuery<FunnelStep[]>({
    queryKey: ["admin_funnel_charts"],
    queryFn: () => fetchApi("/api/admin/funnel"),
  });

  const maxFunnel = funnel.length > 0 ? funnel[0].users : 1;

  if (isLoading)
    return (
      <div className="text-center py-8 text-muted-foreground">
        Yuklanmoqda...
      </div>
    );

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-bold">📊 Tahlil</h2>

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
