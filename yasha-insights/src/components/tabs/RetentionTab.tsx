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
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold">Retention</h2>
        <p className="text-sm text-muted-foreground">
          Cohort analysis & user retention
        </p>
      </div>

      {/* Retention KPIs */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard
          title="D1 Retention"
          value={`${(displayData.d1_retention * 100).toFixed(0)}%`}
          icon={TrendingUp}
          variant="success"
          isLoading={isLoading}
        />
        <StatCard
          title="D7 Retention"
          value={`${(displayData.d7_retention * 100).toFixed(0)}%`}
          icon={BarChart3}
          variant="warning"
          isLoading={isLoading}
        />
        <StatCard
          title="D30 Retention"
          value={`${(displayData.d30_retention * 100).toFixed(0)}%`}
          icon={Calendar}
          isLoading={isLoading}
        />
      </div>

      {/* Retention Funnel */}
      <div className="stat-card">
        <span className="stat-label mb-4 block">Retention Funnel</span>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-8">D0</span>
            <div className="flex-1 h-8 rounded bg-primary relative overflow-hidden">
              <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-primary-foreground">
                100%
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-8">D1</span>
            <div
              className="h-8 rounded bg-success relative overflow-hidden"
              style={{ width: `${displayData.d1_retention * 100}%` }}
            >
              <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-success-foreground">
                {(displayData.d1_retention * 100).toFixed(0)}%
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-8">D7</span>
            <div
              className="h-8 rounded bg-warning relative overflow-hidden"
              style={{ width: `${displayData.d7_retention * 100}%` }}
            >
              <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-warning-foreground">
                {(displayData.d7_retention * 100).toFixed(0)}%
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-8">D30</span>
            <div
              className="h-8 rounded bg-destructive relative overflow-hidden"
              style={{ width: `${displayData.d30_retention * 100}%` }}
            >
              <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-destructive-foreground">
                {(displayData.d30_retention * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Cohort Table */}
      <div className="stat-card overflow-hidden p-0">
        <div className="p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium">Weekly Cohorts</span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Cohort</th>
                <th className="text-center">New</th>
                <th className="text-center">D1</th>
                <th className="text-center">D7</th>
                <th className="text-center">D30</th>
              </tr>
            </thead>
            <tbody>
              {displayData.cohorts.map((cohort) => (
                <tr key={cohort.cohort_date}>
                  <td className="font-medium">
                    {new Date(cohort.cohort_date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </td>
                  <td className="text-center">{cohort.new_users}</td>
                  <td className="text-center">
                    <span
                      className={cn(
                        'retention-cell inline-block min-w-[48px]',
                        getRetentionColor(cohort.d1 / cohort.new_users)
                      )}
                    >
                      {formatPercent(cohort.d1, cohort.new_users)}
                    </span>
                  </td>
                  <td className="text-center">
                    {cohort.d7 > 0 ? (
                      <span
                        className={cn(
                          'retention-cell inline-block min-w-[48px]',
                          getRetentionColor(cohort.d7 / cohort.new_users)
                        )}
                      >
                        {formatPercent(cohort.d7, cohort.new_users)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="text-center">
                    {cohort.d30 > 0 ? (
                      <span
                        className={cn(
                          'retention-cell inline-block min-w-[48px]',
                          getRetentionColor(cohort.d30 / cohort.new_users)
                        )}
                      >
                        {formatPercent(cohort.d30, cohort.new_users)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 text-xs">
        <span className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-success/20 border border-success/50" />
          <span className="text-muted-foreground">{'≥60%'}</span>
        </span>
        <span className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-warning/20 border border-warning/50" />
          <span className="text-muted-foreground">30-60%</span>
        </span>
        <span className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-destructive/20 border border-destructive/50" />
          <span className="text-muted-foreground">{'<30%'}</span>
        </span>
      </div>
    </div>
  );
}

export default RetentionTab;
