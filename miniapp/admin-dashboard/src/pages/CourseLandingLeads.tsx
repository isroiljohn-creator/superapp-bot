import { Card, CardContent } from "@/components/ui/card";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import { toast } from "sonner";

interface CourseLandingStats {
  days: number;
  funnel: Record<string, number>;
  total_leads: number;
  tariff_breakdown: Record<string, number>;
  status_breakdown: Record<string, number>;
}

interface LeadRow {
  id: number;
  name: string;
  phone: string;
  tariff: string | null;
  status: string;
  utm_source: string | null;
  utm_campaign: string | null;
  created_at: string;
}

const FUNNEL_LABELS: Record<string, string> = {
  page_view: "Kirdi",
  modules_view: "Dasturni ko'rdi",
  pricing_view: "Tariflarni ko'rdi",
  lead_form_view: "Formani ko'rdi",
  lead_submitted: "Ariza qoldirdi",
};

const TARIFF_LABELS: Record<string, string> = {
  standard: "Standard",
  premium: "Premium",
  vip: "VIP",
  tanlanmagan: "— Tanlanmagan",
};

const STATUS_LABELS: Record<string, string> = {
  new: "🆕 Yangi",
  contacted: "📞 Bog'lanildi",
  closed: "✅ Yopildi",
};

export default function CourseLandingLeads() {
  const queryClient = useQueryClient();

  const { data: stats, isLoading } = useQuery<CourseLandingStats>({
    queryKey: ["admin_course_landing_stats"],
    queryFn: () => fetchApi("/api/admin/course-landing/stats?days=30"),
  });

  const { data: leads = [], isLoading: leadsLoading } = useQuery<LeadRow[]>({
    queryKey: ["admin_course_landing_leads"],
    queryFn: () => fetchApi("/api/admin/course-landing/leads?limit=200"),
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      fetchApi(`/api/admin/course-landing/leads/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin_course_landing_leads"] });
      queryClient.invalidateQueries({ queryKey: ["admin_course_landing_stats"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const funnelEntries = stats ? Object.entries(stats.funnel) : [];
  const maxCount = funnelEntries.length > 0 ? Math.max(...funnelEntries.map(([, v]) => v), 1) : 1;

  const formatDate = (dateStr: string) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="space-y-3">
      {!isLoading && stats && (
        <div className="grid grid-cols-2 gap-2">
          <Card className="glass-card border-border/30">
            <CardContent className="p-2.5 text-center">
              <p className="text-xl font-bold text-primary leading-none">{stats.total_leads}</p>
              <p className="text-[10px] text-muted-foreground mt-1">Ariza (oxirgi {stats.days} kun)</p>
            </CardContent>
          </Card>
          <Card className="glass-card border-border/30">
            <CardContent className="p-2.5 text-center">
              <p className="text-xl font-bold text-success leading-none">{stats.status_breakdown?.new || 0}</p>
              <p className="text-[10px] text-muted-foreground mt-1">Hali bog'lanilmagan</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <p className="text-xs font-semibold text-muted-foreground mb-2">Sayt voronkasi (noyob tashrif)</p>
          {isLoading ? (
            <div className="text-xs text-muted-foreground text-center py-8">Yuklanmoqda…</div>
          ) : funnelEntries.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-8">Ma'lumot topilmadi</div>
          ) : (
            <div className="space-y-1.5">
              {funnelEntries.map(([stage, count], i) => {
                const pct = Math.max((count / maxCount) * 100, 8);
                const colors = ["#38bdf8", "#22b8cf", "#20c997", "#51cf66", "#fcc419"];
                const color = colors[i % colors.length];
                return (
                  <div key={stage} className="flex items-center gap-2" style={{ height: "32px" }}>
                    <span className="text-xs w-28 md:w-36 text-right truncate flex-shrink-0 text-muted-foreground">
                      {FUNNEL_LABELS[stage] || stage}
                    </span>
                    <div className="flex-1 h-full relative">
                      <div
                        className="h-full rounded flex items-center transition-all duration-500"
                        style={{ width: `${pct}%`, backgroundColor: color, minWidth: "40px" }}
                      >
                        <span className="text-[10px] font-bold text-white px-1.5 drop-shadow whitespace-nowrap">
                          {count.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {!isLoading && stats && (
        <Card className="glass-card border-border/30">
          <CardContent className="p-3">
            <p className="text-xs font-semibold text-muted-foreground mb-2">Tarif bo'yicha</p>
            <div className="space-y-1">
              {Object.entries(stats.tariff_breakdown).map(([tariff, count]) => (
                <div key={tariff} className="flex justify-between text-xs">
                  <span>{TARIFF_LABELS[tariff] || tariff}</span>
                  <span className="font-bold">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <p className="text-xs font-semibold text-muted-foreground mb-2">So'nggi arizalar</p>
          {leadsLoading ? (
            <div className="text-xs text-muted-foreground text-center py-8">Yuklanmoqda…</div>
          ) : leads.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-8">Hali ariza yo'q</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-muted-foreground border-b border-border/30">
                    <th className="py-1.5 pr-2">Ism</th>
                    <th className="py-1.5 pr-2">Telefon</th>
                    <th className="py-1.5 pr-2">Tarif</th>
                    <th className="py-1.5 pr-2">Holat</th>
                    <th className="py-1.5 pr-2">Sana</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map((l) => (
                    <tr key={l.id} className="border-b border-border/10">
                      <td className="py-1.5 pr-2 font-medium">{l.name}</td>
                      <td className="py-1.5 pr-2">
                        <a href={`tel:${l.phone}`} className="text-primary">{l.phone}</a>
                      </td>
                      <td className="py-1.5 pr-2">{TARIFF_LABELS[l.tariff || "tanlanmagan"] || l.tariff}</td>
                      <td className="py-1.5 pr-2">
                        <select
                          className="bg-transparent border border-border/30 rounded px-1 py-0.5 text-xs"
                          value={l.status}
                          onChange={(e) => statusMutation.mutate({ id: l.id, status: e.target.value })}
                        >
                          <option value="new">{STATUS_LABELS.new}</option>
                          <option value="contacted">{STATUS_LABELS.contacted}</option>
                          <option value="closed">{STATUS_LABELS.closed}</option>
                        </select>
                      </td>
                      <td className="py-1.5 pr-2 whitespace-nowrap">{formatDate(l.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
