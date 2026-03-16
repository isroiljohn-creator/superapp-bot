import { useState } from "react";
import { Users, UserCheck, UserX, CreditCard, AlertCircle, ClipboardList, UserPlus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

interface GrowthData {
  date: string;
  users: number;
  total: number;
}

const PERIODS = [
  { label: "7 kun", days: 7 },
  { label: "30 kun", days: 30 },
  { label: "90 kun", days: 90 },
  { label: "Barchasi", days: 365 },
];

export default function DashboardHome() {
  const [selectedDays, setSelectedDays] = useState(30);

  const { data: statsData, isLoading, isError, error } = useQuery({
    queryKey: ["admin_stats"],
    queryFn: () => fetchApi("/api/admin/stats"),
    retry: 1,
    refetchInterval: 30_000,
  });

  const { data: growthData = [], isLoading: growthLoading } = useQuery<GrowthData[]>({
    queryKey: ["admin_daily_growth", selectedDays],
    queryFn: () => fetchApi(`/api/admin/analytics/daily-growth?days=${selectedDays}`),
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
  const displayActivities: any[] = statsData?.recentActivity || [];

  // Growth chart calculations
  const maxTotal = growthData.length > 0 ? Math.max(...growthData.map((d) => d.total)) : 1;
  const minTotal = growthData.length > 0 ? Math.min(...growthData.map((d) => d.total)) : 0;
  const range = maxTotal - minTotal || 1;
  const totalNew = growthData.reduce((s, d) => s + d.users, 0);
  const lastTotal = growthData.length > 0 ? growthData[growthData.length - 1].total : 0;

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

      {/* User Growth Chart with date selector */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-2.5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-semibold">Foydalanuvchilar o'sishi</h3>
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
          {growthLoading ? (
            <div className="h-40 flex items-center justify-center text-xs text-muted-foreground">Yuklanmoqda…</div>
          ) : growthData.length === 0 ? (
            <div className="h-40 flex items-center justify-center text-xs text-muted-foreground">Ma'lumot yo'q</div>
          ) : (
            <>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={growthData} margin={{ top: 4, right: 4, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 9 }}
                      stroke="hsl(var(--muted-foreground))"
                      interval={Math.max(0, Math.floor(growthData.length / 6) - 1)}
                      tickFormatter={(v: string) => v.slice(5)}
                    />
                    <YAxis
                      tick={{ fontSize: 10 }}
                      stroke="hsl(var(--muted-foreground))"
                      width={40}
                      tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}K` : v}
                    />
                    <Tooltip
                      contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "6px", fontSize: 12 }}
                      formatter={(v: number, name: string) => [v.toLocaleString(), name === "total" ? "Jami" : "Yangi"]}
                      labelFormatter={(label: string) => label.slice(5)}
                    />
                    <Bar dataKey="total" fill="hsl(199, 85%, 55%)" radius={[2, 2, 0, 0]} name="total" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>Yangi: <b className="text-foreground">+{totalNew.toLocaleString()}</b> ta</span>
                <span>Jami: <b className="text-foreground">{lastTotal.toLocaleString()}</b> ta</span>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Revenue Chart */}
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
