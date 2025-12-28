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
      <div className="px-2">
        <h2 className="text-2xl font-black tracking-tight text-foreground/90">Sifat va Moslashuv (Quality)</h2>
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
        <div className="glass-card">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🍽️</span>
              <div className="flex flex-col">
                <span className="font-black uppercase tracking-widest text-sm">Menyu Fikrlari</span>
                <span className="text-[10px] font-bold text-muted-foreground mt-0.5">{feedback.menu.users} FOYDALANUVCHI</span>
              </div>
            </div>
            <div className="px-2 py-1 bg-success/10 rounded-lg text-[10px] font-black text-success border border-success/20">MEAL QUALITY</div>
          </div>

          <div className="space-y-5">
            {[
              { label: 'Yaxshi', value: feedback.menu.good, color: 'bg-success', label_eng: 'Good' },
              { label: "O'rtacha", value: feedback.menu.ok, color: 'bg-warning', label_eng: 'OK' },
              { label: 'Yomon', value: feedback.menu.bad, color: 'bg-destructive', label_eng: 'Bad' },
            ].map((item) => (
              <div key={item.label} className="space-y-2">
                <div className="flex items-center justify-between text-[11px] font-black uppercase tracking-wider">
                  <span className="opacity-60">{item.label}</span>
                  <span className="font-mono">{item.value || 0}</span>
                </div>
                <div className="h-2.5 bg-white/5 rounded-full overflow-hidden shadow-inner ring-1 ring-white/5">
                  <div
                    className={cn('h-full transition-all duration-1000 ease-out shadow-lg', item.color)}
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
      <div className="glass-card overflow-hidden p-0 border-destructive/10">
        <div className="p-6 border-b border-white/5 flex items-center justify-between bg-destructive/5">
          <div className="flex items-center gap-3">
            <Heart className="h-5 w-5 text-destructive fill-destructive/20" />
            <span className="font-black uppercase tracking-widest text-sm">Eng sevimli maslahatlar</span>
          </div>
          <span className="text-[10px] font-black text-destructive/60 uppercase tracking-widest">Top Rated Insights</span>
        </div>
        <div className="divide-y divide-white/5">
          {feedback.top_loved_coach.map((msg, i) => (
            <div
              key={msg.coach_msg_key}
              className="group flex items-center gap-4 p-5 transition-all hover:bg-white/5"
            >
              <div className="w-10 h-10 rounded-2xl bg-white/5 flex items-center justify-center font-black text-lg text-muted-foreground group-hover:text-foreground group-hover:scale-110 transition-all border border-white/5">
                {i + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-black uppercase tracking-tight text-foreground/90 group-hover:text-foreground transition-colors">
                  {msg.category.replace(/_/g, ' ')}
                </div>
                <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest opacity-40 group-hover:opacity-60 transition-opacity">
                  {msg.coach_msg_key}
                </div>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 bg-destructive/10 rounded-xl ring-1 ring-destructive/20 group-hover:scale-110 transition-all transform-gpu">
                <Heart className="h-4 w-4 text-destructive fill-current animate-pulse" />
                <span className="font-black font-mono text-destructive text-lg">{msg.love || 0}</span>
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
          {/* Menu Fixes */}
          <div className="glass-card p-8 border-success/10 bg-success/5 relative overflow-hidden group">
            <div className="absolute -right-4 -top-4 opacity-5 group-hover:opacity-10 transition-opacity">
              <CheckCircle2 className="w-24 h-24 text-success" />
            </div>
            <div className="flex items-center justify-between mb-6">
              <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Nutrition Adaptation Rate</span>
              <span className="text-2xl font-mono font-black text-success">{fixRate}%</span>
            </div>
            <div className="h-4 bg-white/5 rounded-full overflow-hidden shadow-inner ring-1 ring-white/5 mb-8">
              <div
                className="h-full bg-success transition-all duration-1000 ease-out shadow-[0_0_20px_rgba(34,197,94,0.4)]"
                style={{ width: `${fixRate}%` }}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col p-3 rounded-2xl bg-white/5 border border-white/5">
                <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-60">Shikoyat</span>
                <span className="text-xl font-black">{adaptation.validation.menu_complaints}</span>
              </div>
              <div className="flex flex-col p-3 rounded-2xl bg-success/10 border border-success/20">
                <span className="text-[10px] font-black text-success/60 uppercase tracking-widest opacity-60">Tuzatildi</span>
                <span className="text-xl font-black text-success">{adaptation.validation.menu_fixed}</span>
              </div>
            </div>
          </div>

          {/* Soft Mode */}
          <div className="glass-card p-8 border-primary/10 bg-primary/5 relative overflow-hidden group">
            <div className="absolute -right-4 -top-4 opacity-5 group-hover:opacity-10 transition-opacity">
              <Zap className="w-24 h-24 text-primary" />
            </div>
            <div className="flex items-center justify-between mb-6">
              <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Workout Fatigue Care</span>
              <span className="text-2xl font-mono font-black text-primary">{softModeRate}%</span>
            </div>
            <div className="h-4 bg-white/5 rounded-full overflow-hidden shadow-inner ring-1 ring-white/5 mb-8">
              <div
                className="h-full bg-primary transition-all duration-1000 ease-out shadow-[0_0_20px_rgba(var(--primary),0.4)]"
                style={{ width: `${softModeRate}%` }}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col p-3 rounded-2xl bg-white/5 border border-white/5">
                <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-60">Charchoq</span>
                <span className="text-xl font-black">{adaptation.validation.workout_tired}</span>
              </div>
              <div className="flex flex-col p-3 rounded-2xl bg-primary/10 border border-primary/20">
                <span className="text-[10px] font-black text-primary/60 uppercase tracking-widest opacity-60">Yumshatildi</span>
                <span className="text-xl font-black text-primary">{adaptation.validation.soft_mode_applied}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Daily Adaptations Chart */}
        <div className="glass-card p-8 bg-primary/5 border-primary/10">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/20 rounded-xl">
                <Activity className="h-4 w-4 text-primary" />
              </div>
              <span className="text-sm font-black uppercase tracking-widest">Kunlik Moslashishlar</span>
            </div>
            <span className="text-[10px] font-black text-primary/60 uppercase tracking-widest opacity-60">Adaptation Volume</span>
          </div>
          <div className="flex items-end justify-between h-32 gap-1.5 px-4 overflow-hidden">
            {adaptation.daily.map((day, i) => (
              <div
                key={day.date}
                className="group relative flex-1"
                style={{ height: '100%' }}
              >
                <div
                  className="absolute bottom-0 w-full bg-gradient-to-t from-primary/40 to-primary rounded-t-xl transition-all duration-1000 ease-out hover:from-primary hover:to-primary group-hover:shadow-[0_0_15px_rgba(var(--primary),0.4)]"
                  style={{
                    height: `${(day.count / (maxDailyAdapt || 1)) * 100}%`,
                    minHeight: '4px',
                    transitionDelay: `${i * 30}ms`
                  }}
                />
                <div className="opacity-0 group-hover:opacity-100 absolute -top-10 left-1/2 -translate-x-1/2 bg-primary text-white text-[10px] font-black px-2 py-1 rounded-md shadow-lg pointer-events-none transition-all duration-300 scale-90 group-hover:scale-100">
                  {day.count}
                </div>
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-6 px-4 text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-40">
            <span>14 kun avval</span>
            <span>Bugun</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default QualityTab;
