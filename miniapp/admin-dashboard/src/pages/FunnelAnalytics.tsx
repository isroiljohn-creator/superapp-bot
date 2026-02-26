import { Card, CardContent } from "@/components/ui/card";

const funnelSteps = [
  { label: "/start", users: 12847, rate: 100 },
  { label: "Ro'yxatdan o'tgan", users: 9635, rate: 75 },
  { label: "Segmentlangan", users: 7227, rate: 75 },
  { label: "Material ochgan", users: 5059, rate: 70 },
  { label: "Video ko'rgan", users: 2529, rate: 50 },
  { label: "To'lovga o'tgan", users: 1517, rate: 60 },
  { label: "To'lov qildi", users: 1234, rate: 81 },
];

export default function FunnelAnalytics() {
  const maxUsers = funnelSteps[0].users;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-bold">Voronka analitikasi</h2>
        <button className="px-3 py-1.5 text-[11px] font-medium bg-secondary text-secondary-foreground rounded-md">
          So'nggi 30 kun
        </button>
      </div>

      <Card className="glass-card border-border/30">
        <CardContent className="p-4 space-y-3">
          {funnelSteps.map((step, i) => {
            const widthPct = (step.users / maxUsers) * 100;
            const dropoff = i > 0
              ? (((funnelSteps[i - 1].users - step.users) / funnelSteps[i - 1].users) * 100).toFixed(1)
              : null;

            return (
              <div key={step.label}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium">{step.label}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold">{step.users.toLocaleString()}</span>
                    {dropoff && (
                      <span className="text-[10px] text-destructive font-medium">
                        −{dropoff}%
                      </span>
                    )}
                  </div>
                </div>
                <div className="h-7 bg-secondary rounded-md overflow-hidden relative">
                  <div
                    className="h-full rounded-md transition-all duration-700"
                    style={{
                      width: `${widthPct}%`,
                      background: `linear-gradient(90deg, hsl(199, 85%, 55%), hsl(199, 85%, ${45 + i * 4}%))`,
                    }}
                  />
                  <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-bold text-muted-foreground">
                    {i > 0 ? `${step.rate}%` : ""}
                  </span>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Umumiy konversiya", value: "9.6%" },
          { label: "Eng katta yo'qotish", value: "Video → To'lovga" },
          { label: "Eng yaxshi bosqich", value: "To'lovga → Sotuv" },
        ].map((s) => (
          <Card key={s.label} className="glass-card border-border/30">
            <CardContent className="p-3 text-center">
              <p className="text-sm font-bold text-primary">{s.value}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">{s.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
