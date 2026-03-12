import { Users, UserCheck, UserX, CreditCard, AlertCircle, ClipboardList, UserPlus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

const typeColors: Record<string, string> = {
  "lead": "bg-primary/10 text-primary",
  "registration_complete": "bg-success/10 text-success",
  "menu_lessons_click": "bg-warning/10 text-warning",
  "payment_success": "bg-success/10 text-success",
};

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
  const totalRevenue = statsData?.kpis?.totalRevenue ?? 0;
  const conversion = statsData?.kpis?.conversion ?? 0;
  const registeredUsers = statsData?.kpis?.registeredUsers ?? 0;
  const startedUsers = statsData?.kpis?.startedUsers ?? 0;

  const kpis = [
    {
      label: "Jami foydalanuvchilar",
      value: isLoading ? "..." : totalUsers.toLocaleString(),
      icon: Users,
      color: "text-primary",
      bg: "bg-primary/10",
    },
    {
      label: "Aktiv",
      value: isLoading ? "..." : activeUsers.toLocaleString(),
      icon: UserCheck,
      color: "text-success",
      bg: "bg-success/10",
      sub: totalUsers > 0 ? `${Math.round(activeUsers / totalUsers * 100)}%` : "0%",
    },
    {
      label: "Ro'yxatdan o'tgan",
      value: isLoading ? "..." : registeredUsers.toLocaleString(),
      icon: ClipboardList,
      color: "text-primary",
      bg: "bg-primary/10",
      sub: totalUsers > 0 ? `${Math.round(registeredUsers / totalUsers * 100)}%` : "0%",
    },
    {
      label: "Ro'yxatdan o'tmagan",
      value: isLoading ? "..." : startedUsers.toLocaleString(),
      icon: UserPlus,
      color: "text-warning",
      bg: "bg-warning/10",
      sub: totalUsers > 0 ? `${Math.round(startedUsers / totalUsers * 100)}%` : "0%",
    },
    {
      label: "Noaktiv",
      value: isLoading ? "..." : inactiveUsers.toLocaleString(),
      icon: UserX,
      color: "text-destructive",
      bg: "bg-destructive/10",
      sub: totalUsers > 0 ? `${Math.round(inactiveUsers / totalUsers * 100)}%` : "0%",
    },
    {
      label: "Yopiq Klub",
      value: isLoading ? "..." : activeSubs.toLocaleString(),
      icon: CreditCard,
      color: "text-warning",
      bg: "bg-warning/10",
      sub: `${conversion}% konv`,
    },
  ];

  const chartData = statsData?.revenueChart7d || [];
  const usersChartData = statsData?.usersChart14d || [];
  const displayActivities: any[] = statsData?.recentActivity || [];

  return (
    <div className="space-y-4">
      {/* Error Banner */}
      {isError && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="p-3 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0" />
            <p className="text-xs text-destructive">
              API xatolik: {(error as Error)?.message || "Ma'lumot yuklanmadi"}
            </p>
          </CardContent>
        </Card>
      )}

      {/* KPI Cards — responsive grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {kpis.map((kpi) => (
          <Card key={kpi.label} className="glass-card border-border/30">
            <CardContent className="p-3">
              <div className={`inline-flex items-center justify-center w-7 h-7 rounded-lg mb-2 ${kpi.bg}`}>
                <kpi.icon className={`h-4 w-4 ${kpi.color}`} />
              </div>
              <p className="text-lg font-bold leading-none">{kpi.value}</p>
              <p className="text-[11px] text-muted-foreground mt-1">{kpi.label}</p>
              {kpi.sub && (
                <p className={`text-[10px] font-medium mt-0.5 ${kpi.color}`}>{kpi.sub}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts row — responsive: stack on mobile, side by side on desktop */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Daily New Users Chart (14 days) */}
        <Card className="glass-card border-border/30">
          <CardContent className="p-3">
            <h3 className="text-sm font-semibold mb-3">📈 Yangi foydalanuvchilar (14 kun)</h3>
            {isLoading ? (
              <div className="h-40 flex items-center justify-center text-xs text-muted-foreground">Yuklanmoqda...</div>
            ) : usersChartData.length === 0 ? (
              <div className="h-40 flex items-center justify-center text-xs text-muted-foreground">Ma'lumot yo'q</div>
            ) : (
              <div className="h-44">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={usersChartData}>
                    <defs>
                      <linearGradient id="userGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(199, 85%, 55%)" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="hsl(199, 85%, 55%)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="day" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
                    <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
                    <Tooltip
                      contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: 12 }}
                      formatter={(value: number) => [`${value} ta`, "Yangi"]}
                    />
                    <Area type="monotone" dataKey="users" stroke="hsl(199, 85%, 55%)" strokeWidth={2} fillOpacity={1} fill="url(#userGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Revenue Chart */}
        <Card className="glass-card border-border/30">
          <CardContent className="p-3">
            <h3 className="text-sm font-semibold mb-3">💰 Tushum (7 kun)</h3>
            {isLoading ? (
              <div className="h-40 flex items-center justify-center text-xs text-muted-foreground">Yuklanmoqda...</div>
            ) : chartData.length === 0 ? (
              <div className="h-40 flex items-center justify-center text-xs text-muted-foreground">Hozircha daromad yo'q</div>
            ) : (
              <div className="h-44">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="day" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
                    <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" tickFormatter={(v) => `${(v / 1000000).toFixed(0)}M`} />
                    <Tooltip
                      contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: 12 }}
                      formatter={(value: number) => [`${(value / 1000000).toFixed(1)}M so'm`, "Tushum"]}
                    />
                    <Bar dataKey="revenue" fill="hsl(142, 60%, 45%)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Aktiv vs Noaktiv progress bar */}
      {!isLoading && totalUsers > 0 && (
        <Card className="glass-card border-border/30">
          <CardContent className="p-3">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold">Aktiv / Noaktiv nisbati</h3>
              <span className="text-[11px] text-muted-foreground">{totalUsers.toLocaleString()} jami</span>
            </div>
            <div className="h-3 w-full rounded-full bg-secondary overflow-hidden flex">
              <div
                className="h-full bg-green-500 transition-all duration-500"
                style={{ width: `${Math.round(activeUsers / totalUsers * 100)}%` }}
              />
              <div
                className="h-full bg-red-400/60 transition-all duration-500"
                style={{ width: `${Math.round(inactiveUsers / totalUsers * 100)}%` }}
              />
            </div>
            <div className="flex items-center gap-4 mt-2">
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
                <span className="text-[11px] text-muted-foreground">Aktiv: {activeUsers.toLocaleString()}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-red-400/60" />
                <span className="text-[11px] text-muted-foreground">Noaktiv: {inactiveUsers.toLocaleString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Activity */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <h3 className="text-sm font-semibold mb-3">🕒 So'nggi faollik</h3>
          {isLoading ? (
            <div className="text-xs text-muted-foreground p-4 text-center">Yuklanmoqda...</div>
          ) : displayActivities.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-4">Hozircha faollik yo'q</div>
          ) : (
            <div className="space-y-2.5">
              {displayActivities.map((a: any) => (
                <div key={a.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <Badge variant="secondary" className={`text-[10px] px-1.5 py-0.5 flex-shrink-0 ${typeColors[a.type] || "bg-secondary text-secondary-foreground"}`}>
                      {a.type}
                    </Badge>
                    <span className="text-xs truncate">{a.text}</span>
                  </div>
                  <span className="text-[10px] text-muted-foreground whitespace-nowrap ml-2">{a.time}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
