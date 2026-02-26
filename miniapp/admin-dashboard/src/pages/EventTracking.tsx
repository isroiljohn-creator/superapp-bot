import { Card, CardContent } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

const topButtons = [
  { name: "Yopiq Klub", clicks: 4821, trend: "+12%" },
  { name: "Bepul Darslar", clicks: 3192, trend: "+8%" },
  { name: "Referal", clicks: 2847, trend: "+15%" },
  { name: "Yordam", clicks: 1523, trend: "-3%" },
  { name: "Kurs haqida", clicks: 1201, trend: "+5%" },
];

const trafficSources = [
  { name: "Instagram", value: 42, color: "hsl(199, 85%, 55%)" },
  { name: "Telegram", value: 28, color: "hsl(199, 85%, 40%)" },
  { name: "Referal", value: 18, color: "hsl(142, 60%, 45%)" },
  { name: "Boshqa", value: 12, color: "hsl(38, 92%, 55%)" },
];

const segmentGoal = [
  { name: "Pul topish", count: 6420 },
  { name: "Mijoz olish", count: 4310 },
  { name: "Avtomatlashtirish", count: 2117 },
];

const segmentLevel = [
  { name: "Boshlang'ich", count: 7200 },
  { name: "Frilanser", count: 3800 },
  { name: "Biznes egasi", count: 1847 },
];

export default function EventTracking() {
  return (
    <div className="space-y-4">
      <h2 className="text-base font-bold">Voqealar va bosishlar</h2>

      {/* Top Buttons */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <h3 className="text-sm font-semibold mb-3">Ko'p bosilgan tugmalar</h3>
          <div className="space-y-2">
            {topButtons.map((btn, i) => (
              <div key={btn.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-muted-foreground w-4">#{i + 1}</span>
                  <span className="text-xs font-medium">{btn.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold">{btn.clicks.toLocaleString()}</span>
                  <span className={`text-[10px] font-medium ${btn.trend.startsWith("+") ? "text-success" : "text-destructive"}`}>
                    {btn.trend}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Traffic Sources */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <h3 className="text-sm font-semibold mb-2">Trafik manbalari</h3>
          <div className="flex items-center gap-4">
            <div className="w-28 h-28">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={trafficSources} cx="50%" cy="50%" innerRadius={28} outerRadius={48} dataKey="value" strokeWidth={0}>
                    {trafficSources.map((entry, idx) => (
                      <Cell key={idx} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex-1 space-y-1.5">
              {trafficSources.map((s) => (
                <div key={s.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full" style={{ background: s.color }} />
                    <span className="text-[11px]">{s.name}</span>
                  </div>
                  <span className="text-[11px] font-semibold">{s.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Segmentation */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <h3 className="text-sm font-semibold mb-2">Maqsad bo'yicha</h3>
          <div className="h-28">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={segmentGoal} layout="vertical">
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={80} stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="count" fill="hsl(199, 85%, 55%)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <h3 className="text-sm font-semibold mb-2">Daraja bo'yicha</h3>
          <div className="h-28">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={segmentLevel} layout="vertical">
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={80} stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="count" fill="hsl(142, 60%, 45%)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
