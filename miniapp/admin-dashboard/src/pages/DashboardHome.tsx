import { TrendingUp, TrendingDown, Users, CreditCard, DollarSign, Percent } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

const defaultKpis = [
  { label: "Jami foydalanuvchilar", id: "totalUsers", value: 0, change: "+0%", up: true, icon: Users },
  { label: "Yopiq Klub", id: "activeSubs", value: 0, change: "+0%", up: true, icon: CreditCard },
  { label: "Tushum", id: "totalRevenue", value: "0 so'm", change: "+0%", up: true, icon: DollarSign },
  { label: "Konversiya", id: "conversion", value: "0%", change: "0%", up: true, icon: Percent },
];

const revenueData7d = [
  { day: "Dush", revenue: 4200000 }, { day: "Sesh", revenue: 5800000 },
  { day: "Chor", revenue: 3900000 }, { day: "Pay", revenue: 7200000 },
  { day: "Jum", revenue: 6100000 }, { day: "Shan", revenue: 8400000 },
  { day: "Yak", revenue: 5500000 },
];

const revenueData30d = [
  { day: "1-h", revenue: 32000000 }, { day: "2-h", revenue: 28000000 },
  { day: "3-h", revenue: 41000000 }, { day: "4-h", revenue: 38000000 },
];

const activities = [
  { id: 1, text: "Foydalanuvchi #4821 ro'yxatdan o'tdi", time: "2 daq oldin", type: "ro'yxatdan o'tish" },
  { id: 2, text: "Foydalanuvchi #3192 videoni ko'rdi", time: "5 daq oldin", type: "video" },
  { id: 3, text: "Foydalanuvchi #7655 97,000 so'm to'ladi", time: "8 daq oldin", type: "to'lov" },
  { id: 4, text: "Foydalanuvchi #1028 materialni ochdi", time: "12 daq oldin", type: "kiritish" },
  { id: 5, text: "Foydalanuvchi #9401 botni boshladi", time: "15 daq oldin", type: "ro'yxatdan o'tish" },
  { id: 6, text: "Foydalanuvchi #6233 197,000 so'm to'ladi", time: "18 daq oldin", type: "to'lov" },
];

const typeColors: Record<string, string> = {
  "ro'yxatdan o'tish": "bg-primary/10 text-primary",
  "video": "bg-warning/10 text-warning",
  "to'lov": "bg-success/10 text-success",
  "kiritish": "bg-accent text-accent-foreground",
};

import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

export default function DashboardHome() {
  const [range, setRange] = useState<"7d" | "30d">("7d");

  const { data: statsData, isLoading } = useQuery({
    queryKey: ["admin_stats"],
    queryFn: () => fetchApi("/api/admin/stats")
  });

  const kpis = statsData?.kpis ? [
    { label: "Jami foydalanuvchilar", value: statsData.kpis.totalUsers.toLocaleString(), change: "+12.5%", up: true, icon: Users },
    { label: "Yopiq Klub", value: statsData.kpis.activeSubs.toLocaleString(), change: "+8.3%", up: true, icon: CreditCard },
    { label: "Tushum", value: `${(statsData.kpis.totalRevenue / 1000000).toFixed(1)}M so'm`, change: "+22.1%", up: true, icon: DollarSign },
    { label: "Konversiya", value: `${statsData.kpis.conversion}%`, change: "-1.2%", up: false, icon: Percent },
  ] : defaultKpis;

  const data = statsData?.revenueChart7d || (range === "7d" ? revenueData7d : revenueData30d);
  const displayActivities = statsData?.recentActivity?.length ? statsData.recentActivity : activities;


  return (
    <div className="space-y-4">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3">
        {kpis.map((kpi) => (
          <Card key={kpi.label} className="glass-card border-border/30">
            <CardContent className="p-3">
              <div className="flex items-center justify-between mb-2">
                <kpi.icon className="h-4 w-4 text-muted-foreground" />
                <span className={`flex items-center gap-0.5 text-xs font-medium ${kpi.up ? "text-success" : "text-destructive"}`}>
                  {kpi.up ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {kpi.change}
                </span>
              </div>
              <p className="text-lg font-bold leading-none">{kpi.value}</p>
              <p className="text-[11px] text-muted-foreground mt-1">{kpi.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Revenue Chart */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">Tushum</h3>
            <div className="flex gap-1">
              {(["7d", "30d"] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => setRange(r)}
                  className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors ${range === r ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
                    }`}
                >
                  {r === "7d" ? "7 kun" : "30 kun"}
                </button>
              ))}
            </div>
          </div>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" tickFormatter={(v) => `${(v / 1000000).toFixed(0)}M`} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                    fontSize: 12,
                  }}
                  formatter={(value: number) => [`${(value / 1000000).toFixed(1)}M so'm`, "Tushum"]}
                />
                <Line type="monotone" dataKey="revenue" stroke="hsl(199, 85%, 55%)" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <h3 className="text-sm font-semibold mb-3">So'nggi faollik</h3>
          {isLoading ? (
            <div className="text-xs text-muted-foreground p-4 text-center">Yuklanmoqda...</div>
          ) : (
            <div className="space-y-2.5">
              {displayActivities.map((a: any) => (
                <div key={a.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className={`text-[10px] px-1.5 py-0.5 ${typeColors[a.type] || "bg-secondary text-secondary-foreground"}`}>
                      {a.type}
                    </Badge>
                    <span className="text-xs">{a.text}</span>
                  </div>
                  <span className="text-[10px] text-muted-foreground whitespace-nowrap ml-2">{a.time}</span>
                </div>
              ))}
              {displayActivities.length === 0 && (
                <div className="text-xs text-muted-foreground text-center py-2">Hozircha faollik yo'q</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
