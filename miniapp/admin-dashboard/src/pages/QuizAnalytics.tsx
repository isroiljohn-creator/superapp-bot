import { Card, CardContent } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

interface QuizStats {
  days: number;
  funnel: Record<string, number>;
  total_submissions: number;
  linked_to_bot: number;
  level_breakdown: Record<string, number>;
  profession_breakdown: Record<string, number>;
}

interface QuizSubmissionRow {
  id: number;
  name: string;
  phone: string;
  profession: string | null;
  level: string;
  correct_count: number;
  utm_source: string | null;
  utm_campaign: string | null;
  linked_to_bot: boolean;
  created_at: string;
}

const FUNNEL_LABELS: Record<string, string> = {
  page_view: "Kirdi",
  profession_selected: "Kasb tanladi",
  quiz_started: "Testni boshladi",
  quiz_completed: "Testni tugatdi",
  contact_view: "Formani ko'rdi",
  submitted: "Ma'lumot qoldirdi",
};

const LEVEL_LABELS: Record<string, string> = {
  boshlangich: "🌱 Boshlang'ich",
  orta: "⚡ O'rta",
  yuqori: "🚀 Yuqori",
};

const PROFESSION_LABELS: Record<string, string> = {
  biznes_egasi: "💼 Biznes egasi",
  oqituvchi: "🎓 O'qituvchi",
  oquvchi: "📚 O'quvchi",
  mutaxassis: "🛠 Mutaxassis",
  shifokor: "🩺 Shifokor",
  ijodkor: "🎨 Ijodkor",
  "noma'lum": "— Noma'lum",
};

export default function QuizAnalytics() {
  const { data: stats, isLoading } = useQuery<QuizStats>({
    queryKey: ["admin_quiz_stats"],
    queryFn: () => fetchApi("/api/admin/quiz/stats?days=30"),
  });

  const { data: submissions = [], isLoading: subsLoading } = useQuery<QuizSubmissionRow[]>({
    queryKey: ["admin_quiz_submissions"],
    queryFn: () => fetchApi("/api/admin/quiz/submissions?limit=100"),
  });

  const funnelEntries = stats ? Object.entries(stats.funnel) : [];
  const maxCount = funnelEntries.length > 0 ? Math.max(...funnelEntries.map(([, v]) => v), 1) : 1;

  const formatDate = (dateStr: string) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="space-y-3">
      {/* Summary cards */}
      {!isLoading && stats && (
        <div className="grid grid-cols-2 gap-2">
          <Card className="glass-card border-border/30">
            <CardContent className="p-2.5 text-center">
              <p className="text-xl font-bold text-primary leading-none">{stats.total_submissions}</p>
              <p className="text-[10px] text-muted-foreground mt-1">Lid (oxirgi {stats.days} kun)</p>
            </CardContent>
          </Card>
          <Card className="glass-card border-border/30">
            <CardContent className="p-2.5 text-center">
              <p className="text-xl font-bold text-success leading-none">{stats.linked_to_bot}</p>
              <p className="text-[10px] text-muted-foreground mt-1">Botga o'tgan</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Funnel bars */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <p className="text-xs font-semibold text-muted-foreground mb-2">Test voronkasi (noyob tashrif)</p>
          {isLoading ? (
            <div className="text-xs text-muted-foreground text-center py-8">Yuklanmoqda…</div>
          ) : funnelEntries.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-8">Ma'lumot topilmadi</div>
          ) : (
            <div className="space-y-1.5">
              {funnelEntries.map(([stage, count], i) => {
                const pct = Math.max((count / maxCount) * 100, 8);
                const colors = ["#38bdf8", "#22b8cf", "#20c997", "#51cf66", "#fcc419", "#ff6b6b"];
                const color = colors[i % colors.length];
                return (
                  <div key={stage} className="flex items-center gap-2" style={{ height: "32px" }}>
                    <span className="text-xs w-24 md:w-32 text-right truncate flex-shrink-0 text-muted-foreground">
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

      {/* Level + profession breakdown */}
      {!isLoading && stats && (
        <div className="grid grid-cols-2 gap-2">
          <Card className="glass-card border-border/30">
            <CardContent className="p-3">
              <p className="text-xs font-semibold text-muted-foreground mb-2">Bilim darajasi</p>
              <div className="space-y-1">
                {Object.entries(stats.level_breakdown).map(([level, count]) => (
                  <div key={level} className="flex justify-between text-xs">
                    <span>{LEVEL_LABELS[level] || level}</span>
                    <span className="font-bold">{count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          <Card className="glass-card border-border/30">
            <CardContent className="p-3">
              <p className="text-xs font-semibold text-muted-foreground mb-2">Kasb</p>
              <div className="space-y-1">
                {Object.entries(stats.profession_breakdown).map(([prof, count]) => (
                  <div key={prof} className="flex justify-between text-xs">
                    <span>{PROFESSION_LABELS[prof] || prof}</span>
                    <span className="font-bold">{count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Submissions table */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <p className="text-xs font-semibold text-muted-foreground mb-2">So'nggi lidlar</p>
          {subsLoading ? (
            <div className="text-xs text-muted-foreground text-center py-8">Yuklanmoqda…</div>
          ) : submissions.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-8">Hali lid yo'q</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-muted-foreground border-b border-border/30">
                    <th className="py-1.5 pr-2">Ism</th>
                    <th className="py-1.5 pr-2">Telefon</th>
                    <th className="py-1.5 pr-2">Kasb</th>
                    <th className="py-1.5 pr-2">Daraja</th>
                    <th className="py-1.5 pr-2">Bot</th>
                    <th className="py-1.5 pr-2">Sana</th>
                  </tr>
                </thead>
                <tbody>
                  {submissions.map((s) => (
                    <tr key={s.id} className="border-b border-border/10">
                      <td className="py-1.5 pr-2 font-medium">{s.name}</td>
                      <td className="py-1.5 pr-2">{s.phone}</td>
                      <td className="py-1.5 pr-2">{PROFESSION_LABELS[s.profession || "noma'lum"] || s.profession}</td>
                      <td className="py-1.5 pr-2">{LEVEL_LABELS[s.level] || s.level} ({s.correct_count}/6)</td>
                      <td className="py-1.5 pr-2">{s.linked_to_bot ? "✅" : "—"}</td>
                      <td className="py-1.5 pr-2 whitespace-nowrap">{formatDate(s.created_at)}</td>
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
