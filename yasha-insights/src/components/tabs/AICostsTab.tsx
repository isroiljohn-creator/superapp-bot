import { Cpu, DollarSign, Zap, TrendingUp } from 'lucide-react';
import { StatCard } from '@/components/StatCard';
import { useAICosts } from '@/hooks/useAnalytics';
import { cn } from '@/lib/utils';

interface AICostsTabProps {
  isLoading?: boolean;
}

export function AICostsTab({ isLoading: externalLoading = false }: AICostsTabProps) {
  const { data, isLoading: internalLoading } = useAICosts();
  const isLoading = externalLoading || internalLoading;

  if (!data && !isLoading) return null;

  const displayData = data || {
    total_tokens: 0,
    total_cost_usd: 0,
    by_feature: [],
    daily: []
  };

  const maxDailyCost = displayData.daily.length > 0
    ? Math.max(...displayData.daily.map((d) => d.cost_usd))
    : 0;

  const featureColors: Record<string, string> = {
    menu: 'bg-chart-1',
    workout: 'bg-chart-2',
    coach: 'bg-chart-3',
  };

  const featureIcons: Record<string, string> = {
    menu: '🍽️',
    workout: '💪',
    coach: '🧠',
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold">AI Costs</h2>
        <p className="text-sm text-muted-foreground">
          Token usage & cost breakdown
        </p>
      </div>

      {/* Total Metrics */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          title="Total Tokens"
          value={(displayData.total_tokens / 1000000).toFixed(2) + 'M'}
          icon={Cpu}
          variant="primary"
          isLoading={isLoading}
        />
        <StatCard
          title="Total Cost"
          value={`$${displayData.total_cost_usd.toFixed(2)}`}
          icon={DollarSign}
          variant="warning"
          isLoading={isLoading}
        />
      </div>

      {/* Cost Per Token */}
      <div className="stat-card">
        <div className="flex items-center justify-between">
          <span className="stat-label">Avg Cost per 1K Tokens</span>
          <Zap className="h-4 w-4 text-warning" />
        </div>
        <div className="stat-value text-warning mt-2">
          ${displayData.total_tokens > 0 ? ((displayData.total_cost_usd / displayData.total_tokens) * 1000).toFixed(4) : '0.0000'}
        </div>
      </div>

      {/* By Feature */}
      <div>
        <h3 className="text-sm font-medium text-muted-foreground mb-3 uppercase tracking-wider">
          Cost by Feature
        </h3>
        <div className="space-y-3">
          {displayData.by_feature.map((feature) => (
            <div
              key={feature.feature}
              className="stat-card flex items-center gap-4"
            >
              <div className="text-2xl">{featureIcons[feature.feature]}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium capitalize">
                    {feature.feature}
                  </span>
                  <span className="font-mono text-sm text-warning">
                    ${feature.cost_usd.toFixed(2)}
                  </span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all',
                      featureColors[feature.feature]
                    )}
                    style={{
                      width: `${displayData.total_cost_usd > 0 ? (feature.cost_usd / displayData.total_cost_usd) * 100 : 0}%`,
                    }}
                  />
                </div>
                <div className="flex justify-between mt-1.5 text-xs text-muted-foreground">
                  <span>{(feature.tokens / 1000).toFixed(0)}K tokens</span>
                  <span>
                    {displayData.total_cost_usd > 0 ? ((feature.cost_usd / displayData.total_cost_usd) * 100).toFixed(0) : 0}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Daily Chart */}
      <div className="stat-card">
        <div className="flex items-center justify-between mb-4">
          <span className="stat-label">Daily Cost (7d)</span>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </div>
        <div className="flex items-end justify-between h-32 gap-1">
          {displayData.daily.map((day) => (
            <div
              key={day.date}
              className="flex-1 flex flex-col items-center gap-1"
            >
              <div
                className="w-full bg-gradient-to-t from-primary to-primary/50 rounded-t transition-all hover:from-primary/90"
                style={{
                  height: `${maxDailyCost > 0 ? (day.cost_usd / maxDailyCost) * 100 : 0}%`,
                  minHeight: '8px',
                }}
              />
              <span className="text-[10px] text-muted-foreground">
                {new Date(day.date).toLocaleDateString('en-US', {
                  weekday: 'short',
                })[0]}
              </span>
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-3 pt-3 border-t border-border text-xs">
          <span className="text-muted-foreground">
            {displayData.daily.length > 0 && new Date(displayData.daily[0].date).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            })}
          </span>
          <span className="text-muted-foreground">
            {displayData.daily.length > 0 && new Date(displayData.daily[displayData.daily.length - 1].date).toLocaleDateString(
              'en-US',
              { month: 'short', day: 'numeric' }
            )}
          </span>
        </div>
      </div>

      {/* Daily Breakdown Table */}
      <div className="stat-card overflow-hidden p-0">
        <div className="p-4 border-b border-border">
          <span className="font-medium">Daily Breakdown</span>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th className="text-right">Tokens</th>
                <th className="text-right">Cost</th>
              </tr>
            </thead>
            <tbody>
              {displayData.daily.slice().reverse().map((day) => (
                <tr key={day.date}>
                  <td>
                    {new Date(day.date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </td>
                  <td className="text-right">
                    {(day.tokens / 1000).toFixed(0)}K
                  </td>
                  <td className="text-right text-warning">
                    ${day.cost_usd.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Spenders */}
      {displayData.top_users && displayData.top_users.length > 0 && (
        <div className="stat-card overflow-hidden p-0">
          <div className="p-4 border-b border-border">
            <span className="font-medium">Top 5 Spenders (30 Days)</span>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th className="text-right">ID</th>
                  <th className="text-right">Spent</th>
                </tr>
              </thead>
              <tbody>
                {displayData.top_users.map((user) => (
                  <tr key={user.user_id}>
                    <td>
                      <div className="flex flex-col">
                        <span className="font-medium">{user.full_name}</span>
                        <span className="text-xs text-muted-foreground">@{user.username || '—'}</span>
                      </div>
                    </td>
                    <td className="text-right font-mono text-xs text-muted-foreground">
                      {user.user_id}
                    </td>
                    <td className="text-right text-warning font-medium">
                      ${user.total_spent.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default AICostsTab;
