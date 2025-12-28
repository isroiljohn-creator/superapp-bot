import { Calendar, TrendingUp, Users, BarChart3 } from 'lucide-react';
import { StatCard } from '@/components/StatCard';
import { useRetention } from '@/hooks/useAnalytics';
import { cn } from '@/lib/utils';

interface RetentionTabProps {
  isLoading?: boolean;
}

export function RetentionTab({ isLoading: externalLoading = false }: RetentionTabProps) {
  const { data, isLoading: internalLoading } = useRetention();
  const isLoading = externalLoading || internalLoading;

  if (!data && !isLoading) return null;

  const displayData = data || {
    d1_retention: 0,
    d7_retention: 0,
    d30_retention: 0,
    cohorts: []
  };

  const getRetentionColor = (rate: number) => {
    if (rate >= 0.6) return 'retention-high';
    if (rate >= 0.3) return 'retention-medium';
    return 'retention-low';
  };

  const formatPercent = (value: number, total: number) => {
    if (total === 0) return '-';
    const percent = (value / total) * 100;
    return `${percent.toFixed(0)}%`;
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="px-2">
        <h2 className="text-2xl font-black tracking-tight text-foreground/90">Qaytuvchanlik (Retention)</h2>
        <p className="text-sm text-muted-foreground font-medium mt-1">
          Kogorta tahlili va foydalanuvchilarning botga sodiqlik darajasi
        </p>
      </div>

      {/* Retention KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6">
        <StatCard
          title="D1 RETENTION"
          value={`${(displayData.d1_retention * 100).toFixed(1)}%`}
          icon={TrendingUp}
          variant="success"
          isLoading={isLoading}
          changeLabel="Target: >40%"
        />
        <StatCard
          title="D7 RETENTION"
          value={`${(displayData.d7_retention * 100).toFixed(1)}%`}
          icon={BarChart3}
          variant="warning"
          isLoading={isLoading}
          changeLabel="Target: >15%"
        />
        <StatCard
          title="D30 RETENTION"
          value={`${(displayData.d30_retention * 100).toFixed(1)}%`}
          icon={Calendar}
          variant="primary"
          isLoading={isLoading}
          changeLabel="Target: >5%"
          className="col-span-2 md:col-span-1"
        />
      </div>

      {/* Retention Funnel */}
      <div className="glass-card p-10 border-primary/5 bg-primary/5">
        <div className="flex items-center justify-between mb-10">
          <div className="flex flex-col">
            <span className="stat-label">Qaytuvchanlik Voronkasi</span>
            <span className="text-[10px] font-black uppercase tracking-widest text-primary/60 mt-0.5">Drop-off Analytics</span>
          </div>
          <div className="px-4 py-1.5 bg-background/50 rounded-full border border-white/5 text-[10px] font-black uppercase tracking-widest">Mathematical View</div>
        </div>

        <div className="space-y-8 max-w-2xl mx-auto">
          {[
            { label: 'Day 0', value: 1, color: 'hsl(var(--primary))', raw: '100% Initialization', icon: Users },
            { label: 'Day 1', value: displayData.d1_retention, color: 'hsl(var(--success))', raw: `${(displayData.d1_retention * 100).toFixed(1)}% Active`, icon: TrendingUp },
            { label: 'Day 7', value: displayData.d7_retention, color: 'hsl(var(--warning))', raw: `${(displayData.d7_retention * 100).toFixed(1)}% Retained`, icon: BarChart3 },
            { label: 'Day 30', value: displayData.d30_retention, color: 'hsl(var(--destructive))', raw: `${(displayData.d30_retention * 100).toFixed(1)}% Loyal`, icon: Calendar },
          ].map((item, i) => (
            <div key={item.label} className="group flex items-center gap-8">
              <div className="flex flex-col items-center w-16 shrink-0">
                <span className="text-[12px] font-black text-foreground uppercase tracking-widest mb-1">{item.label}</span>
                <item.icon className="w-5 h-5 text-muted-foreground opacity-40 group-hover:opacity-100 transition-opacity" />
              </div>
              <div className="flex-1 h-12 bg-background/40 rounded-3xl relative overflow-hidden p-1.5 shadow-inner ring-1 ring-white/5 border border-white/5">
                <div
                  className="h-full rounded-2xl transition-all duration-1000 ease-out shadow-2xl group-hover:animate-pulse"
                  style={{
                    width: `${item.value * 100}%`,
                    backgroundColor: item.color,
                    opacity: 0.7 + (item.value * 0.3)
                  }}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-[11px] font-black text-white mix-blend-difference uppercase tracking-widest">
                    {item.raw}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Cohort Table */}
      <div className="data-table-container">
        <div className="p-6 border-b border-border flex items-center justify-between bg-white/5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-xl">
              <Users className="h-5 w-5 text-primary" />
            </div>
            <div>
              <span className="text-sm font-black uppercase tracking-widest">Haftalik Kogortalar</span>
              <p className="text-[10px] text-muted-foreground font-bold mt-0.5">VAQT BO'YICHA TAHLIL</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-[10px] font-black uppercase tracking-widest">
            <span className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-success/20 ring-1 ring-success/50" />
              Sog'lom
            </span>
            <span className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-destructive/20 ring-1 ring-destructive/50" />
              Xavfli
            </span>
          </div>
        </div>

        <div className="overflow-x-auto scrollbar-hide">
          <table className="data-table">
            <thead>
              <tr>
                <th className="font-black">Kogorta Davri</th>
                <th className="text-center font-black">Yangi</th>
                <th className="text-center font-black">D1 Retention</th>
                <th className="text-center font-black">D7 Retention</th>
                <th className="text-center font-black">D30 Retention</th>
              </tr>
            </thead>
            <tbody>
              {displayData.cohorts.map((cohort) => (
                <tr key={cohort.cohort_date} className="group">
                  <td className="font-bold text-foreground">
                    {new Date(cohort.cohort_date).toLocaleDateString('uz-UZ', {
                      month: 'long',
                      day: 'numeric',
                    })}
                  </td>
                  <td className="text-center font-mono opacity-60 group-hover:opacity-100 transition-opacity">
                    {cohort.new_users}
                  </td>
                  <td className="p-2 text-center h-full">
                    <div
                      className={cn(
                        'retention-cell w-full max-w-[80px] mx-auto',
                        getRetentionColor(cohort.d1 / cohort.new_users)
                      )}
                    >
                      {formatPercent(cohort.d1, cohort.new_users)}
                    </div>
                  </td>
                  <td className="p-2 text-center h-full">
                    {cohort.d7 > 0 ? (
                      <div
                        className={cn(
                          'retention-cell w-full max-w-[80px] mx-auto',
                          getRetentionColor(cohort.d7 / cohort.new_users)
                        )}
                      >
                        {formatPercent(cohort.d7, cohort.new_users)}
                      </div>
                    ) : (
                      <span className="text-[10px] text-muted-foreground/30 font-black tracking-widest">NO DATA</span>
                    )}
                  </td>
                  <td className="p-2 text-center h-full">
                    {cohort.d30 > 0 ? (
                      <div
                        className={cn(
                          'retention-cell w-full max-w-[80px] mx-auto',
                          getRetentionColor(cohort.d30 / cohort.new_users)
                        )}
                      >
                        {formatPercent(cohort.d30, cohort.new_users)}
                      </div>
                    ) : (
                      <span className="text-[10px] text-muted-foreground/30 font-black tracking-widest">NO DATA</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default RetentionTab;
