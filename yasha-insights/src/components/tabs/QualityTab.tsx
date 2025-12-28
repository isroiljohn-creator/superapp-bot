import {
  ThumbsUp,
  Heart,
  Zap,
  Settings2,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
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
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold">Sifat (Quality)</h2>
        <p className="text-sm text-muted-foreground">
          Fikr-mulohazalar va moslashish dvigateli ta'siri
        </p>
      </div>

      {/* Feedback Overview */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          title="Menyu Qoniqishi"
          value={`${menuSatisfaction}%`}
          icon={ThumbsUp}
          variant="success"
          isLoading={isLoading}
        />
        <StatCard
          title="Murabbiy Sevimliligi"
          value={`${coachTotal > 0 ? (((feedback.coach.love || 0) / coachTotal) * 100).toFixed(0) : '0'}%`}
          icon={Heart}
          variant="primary"
          isLoading={isLoading}
        />
      </div>

      {/* Menu Feedback */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-lg">🍽️</span>
          <span className="font-medium">Menyu Fikrlari</span>
          <span className="ml-auto text-xs text-muted-foreground">
            {feedback.menu.users} users
          </span>
        </div>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className="text-xs w-12 text-success">Good</span>
            <div className="flex-1 h-6 bg-secondary rounded overflow-hidden">
              <div
                className="h-full bg-success transition-all"
                style={{ width: `${menuTotal > 0 ? ((feedback.menu.good || 0) / menuTotal) * 100 : 0}%` }}
              />
            </div>
            <span className="font-mono text-xs w-10 text-right">
              {feedback.menu.good || 0}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs w-12 text-warning">OK</span>
            <div className="flex-1 h-6 bg-secondary rounded overflow-hidden">
              <div
                className="h-full bg-warning transition-all"
                style={{ width: `${menuTotal > 0 ? ((feedback.menu.ok || 0) / menuTotal) * 100 : 0}%` }}
              />
            </div>
            <span className="font-mono text-xs w-10 text-right">
              {feedback.menu.ok || 0}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs w-12 text-destructive">Bad</span>
            <div className="flex-1 h-6 bg-secondary rounded overflow-hidden">
              <div
                className="h-full bg-destructive transition-all"
                style={{ width: `${menuTotal > 0 ? ((feedback.menu.bad || 0) / menuTotal) * 100 : 0}%` }}
              />
            </div>
            <span className="font-mono text-xs w-10 text-right">
              {feedback.menu.bad || 0}
            </span>
          </div>
        </div>
      </div>

      {/* Workout Feedback */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-lg">💪</span>
          <span className="font-medium">Mashq Fikrlari</span>
          <span className="ml-auto text-xs text-muted-foreground">
            {feedback.workout.users} users
          </span>
        </div>
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="p-3 rounded-lg bg-success/10 border border-success/20">
            <div className="text-xl font-bold text-success">
              {feedback.workout.strong || 0}
            </div>
            <div className="text-xs text-muted-foreground">Strong</div>
          </div>
          <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
            <div className="text-xl font-bold text-primary">
              {feedback.workout.normal || 0}
            </div>
            <div className="text-xs text-muted-foreground">Normal</div>
          </div>
          <div className="p-3 rounded-lg bg-warning/10 border border-warning/20">
            <div className="text-xl font-bold text-warning">
              {feedback.workout.tired || 0}
            </div>
            <div className="text-xs text-muted-foreground">Tired</div>
          </div>
        </div>
      </div>

      {/* Top Loved Coach Messages */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-4">
          <Heart className="h-4 w-4 text-destructive" />
          <span className="font-medium">Eng sevimli murabbiy maslahatlari</span>
        </div>
        <div className="space-y-2">
          {feedback.top_loved_coach.map((msg, i) => (
            <div
              key={msg.coach_msg_key}
              className="flex items-center gap-3 p-2 rounded-lg bg-secondary/50"
            >
              <span className="text-lg font-bold text-muted-foreground">
                #{i + 1}
              </span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">
                  {msg.category.replace(/_/g, ' ')}
                </div>
                <div className="text-xs text-muted-foreground truncate">
                  {msg.coach_msg_key}
                </div>
              </div>
              <div className="flex items-center gap-1 text-destructive">
                <Heart className="h-3 w-3 fill-current" />
                <span className="font-mono text-sm">{msg.love || 0}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Adaptation Engine */}
      <div className="border-t border-border pt-6">
        <div className="flex items-center gap-2 mb-4">
          <Settings2 className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">Moslashish Dvigateli</h3>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
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
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <StatCard
            title="Yumshoq rejim"
            value={adaptation.soft_mode_users}
            isLoading={isLoading}
          />
          <StatCard
            title="Variantlar alishdi"
            value={adaptation.variant_switches}
            isLoading={isLoading}
          />
        </div>

        {/* Validation Metrics */}
        <div className="stat-card">
          <span className="stat-label mb-4 block">Dvigatelni Tekshirish</span>
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-4 w-4 text-warning" />
              <div className="flex-1">
                <div className="flex justify-between text-sm">
                  <span>Menu Complaints → Fixed</span>
                  <span className="font-mono text-success">{fixRate}%</span>
                </div>
                <div className="h-2 bg-secondary rounded-full mt-1 overflow-hidden">
                  <div
                    className="h-full bg-success transition-all"
                    style={{ width: `${fixRate}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>{adaptation.validation.menu_complaints} complaints</span>
                  <span>{adaptation.validation.menu_fixed} fixed</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-4 w-4 text-success" />
              <div className="flex-1">
                <div className="flex justify-between text-sm">
                  <span>Tired Users → Soft Mode</span>
                  <span className="font-mono text-success">{softModeRate}%</span>
                </div>
                <div className="h-2 bg-secondary rounded-full mt-1 overflow-hidden">
                  <div
                    className="h-full bg-success transition-all"
                    style={{ width: `${softModeRate}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>{adaptation.validation.workout_tired} tired</span>
                  <span>{adaptation.validation.soft_mode_applied} applied</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Daily Adaptations Chart */}
        <div className="stat-card mt-4">
          <div className="flex items-center justify-between mb-4">
            <span className="stat-label">Kunlik Moslashishlar (14 kun)</span>
          </div>
          <div className="flex items-end justify-between h-24 gap-0.5">
            {adaptation.daily.map((day) => (
              <div
                key={day.date}
                className="flex-1 bg-gradient-to-t from-primary to-primary/50 rounded-t transition-all hover:from-primary/80"
                style={{
                  height: `${(day.count / maxDailyAdapt) * 100}%`,
                  minHeight: '4px',
                }}
                title={`${day.date}: ${day.count} adaptations`}
              />
            ))}
          </div>
          <div className="flex justify-between mt-2 text-[10px] text-muted-foreground">
            <span>14 days ago</span>
            <span>Today</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default QualityTab;
