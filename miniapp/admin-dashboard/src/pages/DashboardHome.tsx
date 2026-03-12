import { Users, UserCheck, UserX, CreditCard, AlertCircle, ClipboardList, UserPlus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

export default function DashboardHome() {
  const { data: statsData, isLoading, isError, error } = useQuery({
    queryKey: ["admin_stats"],
    queryFn: () => fetchApi("/api/admin/stats"),
    retry: 1,
    refetchInterval: 30_000,
  });

  const totalUsers = statsData?.kpis?.totalUsers ?? 0;
  const activeUsers = statsData?.kpis?.activeUsers ?? 0;
  const inactiveUsers = statsData?.kpis?.inactiveUsers ?? 0;
  const activeSubs = statsData?.kpis?.activeSubs ?? 0;
  const conversion = statsData?.kpis?.conversion ?? 0;
  const registeredUsers = statsData?.kpis?.registeredUsers ?? 0;
  const startedUsers = statsData?.kpis?.startedUsers ?? 0;

  const kpis = [
    { label: "Jami", value: isLoading ? "…" : totalUsers.toLocaleString(), icon: Users, color: "text-primary", bg: "bg-primary/10" },
    { label: "Aktiv", value: isLoading ? "…" : activeUsers.toLocaleString(), icon: UserCheck, color: "text-success", bg: "bg-success/10", sub: totalUsers > 0 ? `${Math.round(activeUsers / totalUsers * 100)}%` : "" },
    { label: "Noaktiv", value: isLoading ? "…" : inactiveUsers.toLocaleString(), icon: UserX, color: "text-destructive", bg: "bg-destructive/10", sub: totalUsers > 0 ? `${Math.round(inactiveUsers / totalUsers * 100)}%` : "" },
    { label: "Ro'yxatli", value: isLoading ? "…" : registeredUsers.toLocaleString(), icon: ClipboardList, color: "text-primary", bg: "bg-primary/10", sub: totalUsers > 0 ? `${Math.round(registeredUsers / totalUsers * 100)}%` : "" },
    { label: "Kutilmoqda", value: isLoading ? "…" : startedUsers.toLocaleString(), icon: UserPlus, color: "text-warning", bg: "bg-warning/10", sub: totalUsers > 0 ? `${Math.round(startedUsers / totalUsers * 100)}%` : "" },
    { label: "Klub", value: isLoading ? "…" : activeSubs.toLocaleString(), icon: CreditCard, color: "text-warning", bg: "bg-warning/10", sub: `${conversion}%` },
  ];

  const chartData = statsData?.revenueChart7d || [];
  const usersChartData = statsData?.usersChart14d || [];
  const displayActivities: any[] = statsData?.recentActivity || [];

  return (
    <div className="space-y-3">
      {isError && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="p-2.5 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0" />
            <p className="text-xs text-destructive truncate">
              {(error as Error)?.message || "Ma'lumot yuklanmadi"}
            </p>
          </CardContent>
        </Card>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
        {kpis.map((kpi) => (
          <Card key={kpi.label} className="glass-card border-border/30">
            <CardContent className="p-2.5">
              <div className={`inline-flex items-center justify-center w-7 h-7 rounded-lg mb-1.5 ${kpi.bg}`}>
                <kpi.icon className={`h-3.5 w-3.5 ${kpi.color}`} />
              </div>
              <p className="text-lg font-bold leading-none">{kpi.value}</p>
              <p className="text-[10px] text-muted-foreground mt-1">{kpi.label}</p>
              {kpi.sub && <p className={`text-[10px] font-medium ${kpi.color}`}>{kpi.sub}</p>}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Progress bar */}
      {!isLoading && totalUsers > 0 && (
        <Card className="glass-card border-border/30">
          <CardContent className="p-2.5">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold">Aktiv / Noaktiv</span>
              <span className="text-[10px] text-muted-foreground">{totalUsers.toLocaleString()} jami</span>
            </div>
            <div className="h-2.5 w-full rounded-full bg-secondary overflow-hidden flex">
              <div className="h-full bg-green-500" style={{ width: `${Math.round(activeUsers / totalUsers * 100)}%` }} />
              <div className="h-full bg-red-400/60" style={{ width: `${Math.round(inactiveUsers / totalUsers * 100)}%` }} />
            </div>
            <div className="flex items-center gap-3 mt-1.5">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-[10px] text-muted-foreground">{activeUsers}</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-red-400/60" />
                <span className="text-[10px] text-muted-foreground">{inactiveUsers}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Card className="glass-card border-border/30">
          <CardContent className="p-2.5">
            <h3 className="text-xs font-semibold mb-2">Yangi foydalanuvchilar (14 kun)</h3>
            {isLoading ? (
              <div className="h-36 flex items-center justify-center text-xs text-muted-foreground">Yuklanmoqda…</div>
            ) : usersChartData.length === 0 ? (
              <div className="h-36 flex items-center justify-center text-xs text-muted-foreground">Ma'lumot yo'q</div>
            ) : (
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={usersChartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="userGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(199, 85%, 55%)" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="hsl(199, 85%, 55%)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="day" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" interval="preserveStartEnd" />
                    <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" width={30} />
                    <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "6px", fontSize: 12 }} formatter={(v: number) => [`${v}`, "Yangi"]} />
                    <Area type="monotone" dataKey="users" stroke="hsl(199, 85%, 55%)" strokeWidth={2} fill="url(#userGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="glass-card border-border/30">
          <CardContent className="p-2.5">
            <h3 className="text-xs font-semibold mb-2">Tushum (7 kun)</h3>
            {isLoading ? (
              <div className="h-36 flex items-center justify-center text-xs text-muted-foreground">Yuklanmoqda…</div>
            ) : chartData.length === 0 ? (
              <div className="h-36 flex items-center justify-center text-xs text-muted-foreground">Hozircha daromad yo'q</div>
            ) : (
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="day" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
                    <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" width={30} tickFormatter={(v) => v >= 1000000 ? `${(v / 1000000).toFixed(0)}M` : v >= 1000 ? `${(v / 1000).toFixed(0)}K` : v} />
                    <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "6px", fontSize: 12 }} formatter={(v: number) => [v >= 1000000 ? `${(v / 1000000).toFixed(1)}M` : v.toLocaleString(), "so'm"]} />
                    <Bar dataKey="revenue" fill="hsl(142, 60%, 45%)" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-2.5">
          <h3 className="text-xs font-semibold mb-2">So'nggi faollik</h3>
          {isLoading ? (
            <div className="text-xs text-muted-foreground p-3 text-center">Yuklanmoqda…</div>
          ) : displayActivities.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-3">Hozircha faollik yo'q</div>
          ) : (
            <div className="space-y-2">
              {displayActivities.map((a: any) => (
                <div key={a.id} className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 min-w-0 flex-1">
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0 flex-shrink-0">
                      {a.type?.replace(/_/g, " ").slice(0, 15)}
                    </Badge>
                    <span className="text-xs truncate">{a.text}</span>
                  </div>
                  <span className="text-[10px] text-muted-foreground whitespace-nowrap">{a.time}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
