import { Cpu, DollarSign, Zap, TrendingUp, Sparkles } from 'lucide-react';
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
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="px-2">
        <h2 className="text-2xl font-black tracking-tight text-foreground/90">AI Xarajatlari (AI Costs)</h2>
        <p className="text-sm text-muted-foreground font-medium mt-1">
          Sun'iy intellekt tokenlari iste'moli va moliyaviy tahlil
        </p>
      </div>

      {/* Total Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <StatCard
          title="Jami Tokenlar"
          value={(displayData.total_tokens / 1000000).toFixed(2) + 'M'}
          icon={Cpu}
          variant="primary"
          isLoading={isLoading}
          changeLabel="Million tokenlarda"
        />
        <StatCard
          title="Jami Xarajat"
          value={`$${displayData.total_cost_usd.toFixed(2)}`}
          icon={DollarSign}
          variant="warning"
          isLoading={isLoading}
          changeLabel="USD (OpenAI/Anthropic)"
        />
      </div>

      {/* Cost Per Token & Efficiency */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass-card flex items-center justify-between p-8">
          <div>
            <span className="stat-label">1M Token Narxi</span>
            <div className="stat-value text-4xl mt-1 text-warning">
              ${displayData.total_tokens > 0 ? ((displayData.total_cost_usd / displayData.total_tokens) * 1000000).toFixed(2) : '0.00'}
            </div>
          </div>
          <div className="p-4 bg-warning/10 rounded-2xl ring-1 ring-warning/20">
            <Zap className="h-8 w-8 text-warning" />
          </div>
        </div>
        <div className="glass-card flex items-center justify-between p-8 border-primary/20">
          <div>
            <span className="stat-label">AI Samaradorligi</span>
            <div className="stat-value text-4xl mt-1 text-primary">
              {displayData.total_tokens > 0 ? (displayData.total_tokens / displayData.total_cost_usd / 1000).toFixed(0) : '0'}K
            </div>
          </div>
          <div className="p-4 bg-primary/10 rounded-2xl ring-1 ring-primary/20">
            <TrendingUp className="h-8 w-8 text-primary" />
          </div>
        </div>
      </div>

      {/* By Feature Breakdown */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 px-2">
          <Sparkles className="w-4 h-4 text-warning" />
          <h3 className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em]">
            Funksiyalar bo'yicha tahlil
          </h3>
        </div>
        <div className="grid grid-cols-1 gap-3">
          {displayData.by_feature.map((feature) => (
            <div
              key={feature.feature}
              className="glass-card group flex items-center gap-6 py-5 px-6"
            >
              <div className="text-4xl filter grayscale group-hover:grayscale-0 transition-all duration-500 scale-110">
                {featureIcons[feature.feature] || '⚡'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex flex-col">
                    <span className="font-black text-lg uppercase tracking-tight">
                      {feature.feature}
                    </span>
                    <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mt-0.5 opacity-60">
                      Module Usage Report
                    </span>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="stat-value text-2xl" style={{ backgroundImage: 'none', color: 'hsl(var(--warning))' }}>
                      ${feature.cost_usd.toFixed(3)}
                    </span>
                    <span className="text-[10px] font-mono text-muted-foreground mt-0.5 opacity-60">
                      {(feature.tokens / 1000).toFixed(0)}K TOKENS
                    </span>
                  </div>
                </div>
                <div className="h-2.5 bg-white/5 rounded-full overflow-hidden shadow-inner ring-1 ring-white/5">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(var(--warning),0.3)]',
                      featureColors[feature.feature] || 'bg-primary'
                    )}
                    style={{
                      width: `${displayData.total_cost_usd > 0 ? (feature.cost_usd / displayData.total_cost_usd) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Daily Chart */}
      <div className="glass-card p-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex flex-col">
            <span className="stat-label">Kunlik Xarajat (7 kun)</span>
            <span className="text-[10px] text-muted-foreground font-bold mt-1 uppercase tracking-widest">Financial Trending</span>
          </div>
          <TrendingUp className="h-5 w-5 text-primary" />
        </div>

        <div className="flex items-end justify-between h-48 gap-3">
          {displayData.daily.map((day) => (
            <div
              key={day.date}
              className="group flex-1 flex flex-col items-center gap-3"
            >
              <div className="relative w-full flex flex-col items-center">
                <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-10 bg-primary text-white text-[10px] font-black px-2 py-1 rounded-md shadow-lg pointer-events-none z-10 scale-90 group-hover:scale-100 origin-bottom duration-300">
                  ${day.cost_usd.toFixed(2)}
                </div>
                <div
                  className="w-full bg-gradient-to-t from-primary/80 to-primary rounded-2xl transition-all duration-700 hover:scale-x-110 hover:shadow-[0_0_20px_rgba(34,197,94,0.3)] cursor-pointer"
                  style={{
                    height: `${maxDailyCost > 0 ? (day.cost_usd / maxDailyCost) * 100 : 0}%`,
                    minHeight: '8px',
                  }}
                />
              </div>
              <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-40 group-hover:opacity-100 group-hover:text-primary transition-all">
                {new Date(day.date).toLocaleDateString('uz-UZ', { weekday: 'short' })}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Tables Row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Daily Breakdown Table */}
        <div className="data-table-container">
          <div className="p-6 border-b border-white/5 bg-white/5 flex items-center justify-between">
            <span className="text-sm font-black uppercase tracking-widest">Kunlik Dinamika</span>
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest opacity-60">History Detail</span>
          </div>
          <div className="overflow-x-auto scrollbar-hide">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="font-black">Sana</th>
                  <th className="text-right font-black">Tokenlar</th>
                  <th className="text-right font-black">Xarajat</th>
                </tr>
              </thead>
              <tbody>
                {displayData.daily.slice().reverse().map((day) => (
                  <tr key={day.date} className="group transition-colors active:bg-white/5 select-none">
                    <td className="font-bold text-foreground opacity-80 group-hover:opacity-100">
                      {new Date(day.date).toLocaleDateString('uz-UZ', {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </td>
                    <td className="text-right font-mono text-muted-foreground">
                      {(day.tokens / 1000).toFixed(0)}K
                    </td>
                    <td className="text-right text-warning font-black">
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
          <div className="data-table-container border-primary/10">
            <div className="p-6 border-b border-white/5 bg-primary/5 flex items-center justify-between">
              <span className="text-sm font-black uppercase tracking-widest text-primary">Eng faollar (30 kun)</span>
              <span className="text-[10px] font-bold text-primary/60 uppercase tracking-widest">Power Users</span>
            </div>
            <div className="overflow-x-auto scrollbar-hide">
              <table className="data-table">
                <thead>
                  <tr>
                    <th className="font-black">Foydalanuvchi</th>
                    <th className="text-right font-black">Narx</th>
                  </tr>
                </thead>
                <tbody>
                  {displayData.top_users.map((user) => (
                    <tr key={user.user_id} className="group">
                      <td>
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center font-black text-xs text-primary ring-1 ring-white/10 group-hover:scale-110 transition-transform">
                            {user.full_name[0]}
                          </div>
                          <div className="flex flex-col truncate min-w-0">
                            <span className="font-bold text-sm truncate">{user.full_name}</span>
                            <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-50 truncate">@{user.username || 'user'}</span>
                          </div>
                        </div>
                      </td>
                      <td className="text-right text-warning font-black text-base">
                        ${user.total_spent.toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AICostsTab;
