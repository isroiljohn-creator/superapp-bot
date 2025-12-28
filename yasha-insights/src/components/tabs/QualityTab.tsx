import {
  ThumbsUp,
  Heart,
  Zap,
  Settings2,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  Activity,
} from 'lucide-react';
import { StatCard } from '@/components/StatCard';
import { useFeedback, useAdaptation } from '@/hooks/useAnalytics';
import { cn } from '@/lib/utils';

interface QualityTabProps {
  isLoading?: boolean;
}

export function QualityTab({ isLoading: externalLoading = false }: QualityTabProps) {
  const { data: feedbackData, isLoading: feedbackLoading } = useFeedback();
  const { data: adaptationData, isLoading: adaptationLoading } = useAdaptation();
  const isLoading = externalLoading || feedbackLoading || adaptationLoading;

  if ((!feedbackData || !adaptationData) && !isLoading) return null;

  const feedback = feedbackData || {
    menu: { users: 0 },
    workout: { users: 0 },
    coach: { users: 0 },
    top_loved_coach: []
  };
  const adaptation = adaptationData || {
    adapted_users: 0,
    kcal_adjusted: 0,
    soft_mode_users: 0,
    variant_switches: 0,
    daily: [],
    validation: {
      menu_complaints: 0,
      menu_fixed: 0,
      workout_tired: 0,
      soft_mode_applied: 0
    }
  };

  const menuTotal = (feedback.menu.good || 0) + (feedback.menu.ok || 0) + (feedback.menu.bad || 0);
  const workoutTotal = (feedback.workout.strong || 0) + (feedback.workout.normal || 0) + (feedback.workout.tired || 0);
  const coachTotal = (feedback.coach.like || 0) + (feedback.coach.love || 0) + (feedback.coach.meh || 0);

  const menuSatisfaction = menuTotal > 0 ? (((feedback.menu.good || 0) / menuTotal) * 100).toFixed(0) : '0';
  const fixRate = adaptation.validation.menu_complaints > 0
    ? ((adaptation.validation.menu_fixed / adaptation.validation.menu_complaints) * 100).toFixed(0)
    : '0';
  const softModeRate = adaptation.validation.workout_tired > 0
    ? ((adaptation.validation.soft_mode_applied / adaptation.validation.workout_tired) * 100).toFixed(0)
    : '0';

  const maxDailyAdapt = adaptation.daily.length > 0 ? Math.max(...adaptation.daily.map((d) => d.count)) : 0;

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="px-1">
        <h2 className="text-3xl font-black tracking-tight text-foreground">Sifat va Moslashuv (Quality)</h2>
        <p className="text-sm text-muted-foreground font-medium mt-1">
          Fikr-mulohazalar monitoringi va AI moslashish samaradorligi
        </p>
      </div>

      {/* Feedback Overview */}
      <div className="grid grid-cols-2 md:grid-cols-2 gap-4 md:gap-6">
        <StatCard
          title="Menyu Qoniqishi"
          value={`${menuSatisfaction}%`}
          icon={ThumbsUp}
          variant="success"
          isLoading={isLoading}
          changeLabel="Target: >85%"
        />
        <StatCard
          title="Murabbiy Sevimliligi"
          value={`${coachTotal > 0 ? (((feedback.coach.love || 0) / coachTotal) * 100).toFixed(0) : '0'}%`}
          icon={Heart}
          variant="primary"
          isLoading={isLoading}
          changeLabel="Target: >70%"
        />
      </div>

      {/* Feedback Modules */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Menu Feedback */}
        <div className="glass-card p-10">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <span className="text-3xl">🍽️</span>
              <div className="flex flex-col">
                <span className="font-black uppercase tracking-[0.15em] text-[11px] text-foreground/70">Menyu Fikrlari</span>
                <span className="text-[10px] font-black text-muted-foreground mt-0.5 uppercase tracking-widest">{feedback.menu.users} FOYDALANUVCHI</span>
              </div>
            </div>
            <div className="px-4 py-1.5 bg-success/10 rounded-full text-[10px] font-black text-success border border-success/20 uppercase tracking-widest shadow-sm">MEAL QUALITY</div>
          </div>

          <div className="space-y-5">
            {[
              { label: 'Yaxshi', value: feedback.menu.good, color: 'bg-success', label_eng: 'Good' },
              { label: "O'rtacha", value: feedback.menu.ok, color: 'bg-warning', label_eng: 'OK' },
              { label: 'Yomon', value: feedback.menu.bad, color: 'bg-destructive', label_eng: 'Bad' },
            ].map((item) => (
              <div key={item.label} className="space-y-3">
                <div className="flex items-center justify-between text-[11px] font-black uppercase tracking-[0.1em]">
                  <span className="opacity-70">{item.label}</span>
                  <span className="font-mono text-foreground">{item.value || 0}</span>
                </div>
                <div className="h-3 bg-muted rounded-full overflow-hidden shadow-inner border border-border/50">
                  <div
                    className={cn('h-full transition-all duration-1000 ease-out shadow-sm group-hover:glow-primary', item.color)}
                    style={{ width: `${menuTotal > 0 ? ((item.value || 0) / menuTotal) * 100 : 0}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Workout Feedback */}
        <div className="glass-card">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <span className="text-2xl">💪</span>
              <div className="flex flex-col">
                <span className="font-black uppercase tracking-widest text-sm">Mashq Fikrlari</span>
                <span className="text-[10px] font-bold text-muted-foreground mt-0.5">{feedback.workout.users} FOYDALANUVCHI</span>
              </div>
            </div>
            <div className="px-2 py-1 bg-primary/10 rounded-lg text-[10px] font-black text-primary border border-primary/20">EFFORT LEVEL</div>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {[
              { label: 'Kuchli Energy', value: feedback.workout.strong, color: 'bg-success/10 text-success ring-success/20', icon: Zap },
              { label: 'Normal Holat', value: feedback.workout.normal, color: 'bg-primary/10 text-primary ring-primary/20', icon: CheckCircle2 },
              { label: 'Charchoq Sezildi', value: feedback.workout.tired, color: 'bg-warning/10 text-warning ring-warning/20', icon: AlertCircle },
            ].map((item) => (
              <div key={item.label} className={cn("flex items-center justify-between p-4 rounded-2xl ring-1 transition-all hover:bg-white/5", item.color)}>
                <div className="flex items-center gap-3">
                  <item.icon className="w-4 h-4" />
                  <span className="text-xs font-black uppercase tracking-widest">{item.label}</span>
                </div>
                <span className="text-xl font-black font-mono">{item.value || 0}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Loved Coach Messages */}
      <div className="glass-card overflow-hidden p-0 border-destructive/20 relative">
        <div className="p-8 border-b border-border flex items-center justify-between bg-destructive/10">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-destructive/20 rounded-2xl border border-destructive/30">
              <Heart className="h-6 w-6 text-destructive fill-destructive/20" />
            </div>
            <div>
              <span className="font-black uppercase tracking-[0.15em] text-[11px] text-foreground">Eng sevimli maslahatlar</span>
              <p className="text-[10px] font-black text-destructive/70 uppercase tracking-widest mt-0.5 opacity-60">Top Rated Insights</p>
            </div>
          </div>
          <div className="px-5 py-2 bg-background/50 rounded-full border border-destructive/20 text-[10px] font-black uppercase tracking-widest text-destructive">Audience Choice</div>
        </div>
        <div className="divide-y divide-border">
          {feedback.top_loved_coach.map((msg, i) => (
            <div
              key={msg.coach_msg_key}
              className="group flex items-center gap-6 p-6 transition-all hover:bg-muted/50"
            >
              <div className="w-12 h-12 rounded-2xl bg-muted border border-border flex items-center justify-center font-black text-xl text-muted-foreground group-hover:text-foreground group-hover:border-primary/50 group-hover:scale-105 transition-all shadow-sm">
                {i + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-base font-black uppercase tracking-tight text-foreground/90 group-hover:text-foreground transition-colors">
                  {msg.category.replace(/_/g, ' ')}
                </div>
                <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-40 group-hover:opacity-60 transition-opacity mt-1">
                  {msg.coach_msg_key}
                </div>
              </div>
              <div className="flex items-center gap-3 px-5 py-2.5 bg-destructive/10 rounded-2xl border border-destructive/20 group-hover:scale-105 transition-all transform-gpu shadow-sm group-hover:border-destructive/40">
                <Heart className="h-5 w-5 text-destructive fill-current animate-pulse" />
                <span className="font-black font-mono text-destructive text-2xl leading-none">{msg.love || 0}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Adaptation Engine */}
      <div className="space-y-6 pt-4">
        <div className="flex items-center gap-3 px-2">
          <div className="p-2 bg-primary/10 rounded-xl">
            <Settings2 className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="text-lg font-black uppercase tracking-tight">Moslashish Dvigateli</h3>
            <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest -mt-1 opacity-60">AI Engine Performance</p>
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          <StatCard
            title="Moslashganlar"
            value={adaptation.adapted_users}
            icon={Zap}
            variant="primary"
            isLoading={isLoading}
          />
          <StatCard
            title="Kcal O'zgartirildi"
            value={adaptation.kcal_adjusted}
            icon={TrendingUp}
            isLoading={isLoading}
          />
          <StatCard
            title="Yumshoq rejim"
            value={adaptation.soft_mode_users}
            isLoading={isLoading}
            variant="warning"
          />
          <StatCard
            title="Shtat o'zgardi"
            value={adaptation.variant_switches}
            isLoading={isLoading}
          />
        </div>

        {/* Validation Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8">
          {/* Menu Fixes */}
          <div className="glass-card p-10 border-success/20 bg-success/10 relative overflow-hidden group">
            <div className="absolute -right-4 -top-4 opacity-5 group-hover:opacity-10 transition-opacity">
              <CheckCircle2 className="w-32 h-32 text-success" />
            </div>
            <div className="flex items-center justify-between mb-8">
              <span className="text-[11px] font-black uppercase tracking-[0.15em] text-muted-foreground/70">Nutrition Adaptation Rate</span>
              <span className="text-3xl font-mono font-black text-success">{fixRate}%</span>
            </div>
            <div className="h-4 bg-muted rounded-full overflow-hidden shadow-inner border border-border/50 mb-10">
              <div
                className="h-full bg-success transition-all duration-1000 ease-out shadow-lg group-hover:glow-success"
                style={{ width: `${fixRate}%` }}
              />
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div className="flex flex-col p-4 rounded-2xl bg-muted border border-border group-hover:border-border transition-colors">
                <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-60">Shikoyat</span>
                <span className="text-2xl font-black mt-1">{adaptation.validation.menu_complaints}</span>
              </div>
              <div className="flex flex-col p-4 rounded-2xl bg-success/20 border border-success/30 group-hover:border-success/50 transition-colors">
                <span className="text-[10px] font-black text-success/60 uppercase tracking-widest opacity-60">Tuzatildi</span>
                <span className="text-2xl font-black text-success mt-1">{adaptation.validation.menu_fixed}</span>
              </div>
            </div>
          </div>

          {/* Soft Mode */}
          <div className="glass-card p-10 border-primary/20 bg-primary/10 relative overflow-hidden group">
            <div className="absolute -right-4 -top-4 opacity-5 group-hover:opacity-10 transition-opacity">
              <Zap className="w-32 h-32 text-primary" />
            </div>
            <div className="flex items-center justify-between mb-8">
              <span className="text-[11px] font-black uppercase tracking-[0.15em] text-muted-foreground/70">Workout Fatigue Care</span>
              <span className="text-3xl font-mono font-black text-primary">{softModeRate}%</span>
            </div>
            <div className="h-4 bg-muted rounded-full overflow-hidden shadow-inner border border-border/50 mb-10">
              <div
                className="h-full bg-primary transition-all duration-1000 ease-out shadow-lg group-hover:glow-primary"
                style={{ width: `${softModeRate}%` }}
              />
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div className="flex flex-col p-4 rounded-2xl bg-muted border border-border group-hover:border-border transition-colors">
                <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-60">Charchoq</span>
                <span className="text-2xl font-black mt-1">{adaptation.validation.workout_tired}</span>
              </div>
              <div className="flex flex-col p-4 rounded-2xl bg-primary/20 border border-primary/30 group-hover:border-primary/50 transition-colors">
                <span className="text-[10px] font-black text-primary/60 uppercase tracking-widest opacity-60">Yumshatildi</span>
                <span className="text-2xl font-black text-primary mt-1">{adaptation.validation.soft_mode_applied}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Daily Adaptations Chart */}
        <div className="glass-card p-10 bg-primary/10 border-primary/20">
          <div className="flex items-center justify-between mb-10">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary/20 rounded-2xl border border-primary/30">
                <Activity className="h-6 w-6 text-primary" />
              </div>
              <div>
                <span className="text-[11px] font-black uppercase tracking-[0.15em] text-foreground">Kunlik Moslashishlar</span>
                <p className="text-[10px] font-black text-primary/70 uppercase tracking-widest mt-0.5 opacity-60">Adaptation Volume</p>
              </div>
            </div>
            <span className="px-4 py-1.5 bg-background/50 rounded-full border border-primary/20 text-[10px] font-black uppercase tracking-widest text-primary">Live Tracking</span>
          </div>
          <div className="flex items-end justify-between h-40 gap-2 px-6 overflow-hidden">
            {adaptation.daily.map((day, i) => (
              <div
                key={day.date}
                className="group relative flex-1"
                style={{ height: '100%' }}
              >
                <div
                  className="absolute bottom-0 w-full bg-gradient-to-t from-primary/60 to-primary rounded-t-2xl transition-all duration-1000 ease-out hover:from-primary hover:to-primary group-hover:glow-primary shadow-lg border-x border-t border-primary/30"
                  style={{
                    height: `${(day.count / (maxDailyAdapt || 1)) * 100}%`,
                    minHeight: '8px',
                    transitionDelay: `${i * 30}ms`
                  }}
                />
                <div className="opacity-0 group-hover:opacity-100 absolute -top-12 left-1/2 -translate-x-1/2 bg-primary text-white text-[10px] font-black px-2.5 py-1.5 rounded-xl shadow-xl pointer-events-none transition-all duration-300 scale-75 group-hover:scale-100 origin-bottom border border-white/20 whitespace-nowrap z-20">
                  {day.count} Akt
                </div>
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-8 px-6 text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-40">
            <span className="flex items-center gap-2 pt-2 border-t border-border w-32">14 kun avval</span>
            <span className="flex items-center gap-2 pt-2 border-t border-border w-32 justify-end">Bugun</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default QualityTab;
