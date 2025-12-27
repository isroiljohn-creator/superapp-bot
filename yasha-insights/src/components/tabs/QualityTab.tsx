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
import { mockFeedback, mockAdaptation } from '@/hooks/useAnalytics';
import { cn } from '@/lib/utils';

interface QualityTabProps {
  isLoading?: boolean;
}

export function QualityTab({ isLoading = false }: QualityTabProps) {
  const feedback = mockFeedback;
  const adaptation = mockAdaptation;

  const menuTotal = feedback.menu.good! + feedback.menu.ok! + feedback.menu.bad!;
  const workoutTotal =
    feedback.workout.strong! + feedback.workout.normal! + feedback.workout.tired!;
  const coachTotal =
    feedback.coach.like! + feedback.coach.love! + feedback.coach.meh!;

  const menuSatisfaction = ((feedback.menu.good! / menuTotal) * 100).toFixed(0);
  const fixRate = ((adaptation.validation.menu_fixed / adaptation.validation.menu_complaints) * 100).toFixed(0);
  const softModeRate = ((adaptation.validation.soft_mode_applied / adaptation.validation.workout_tired) * 100).toFixed(0);

  const maxDailyAdapt = Math.max(...adaptation.daily.map((d) => d.count));

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold">Quality</h2>
        <p className="text-sm text-muted-foreground">
          Feedback & adaptation engine impact
        </p>
      </div>

      {/* Feedback Overview */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          title="Menu Satisfaction"
          value={`${menuSatisfaction}%`}
          icon={ThumbsUp}
          variant="success"
          isLoading={isLoading}
        />
        <StatCard
          title="Coach Love Rate"
          value={`${((feedback.coach.love! / coachTotal) * 100).toFixed(0)}%`}
          icon={Heart}
          variant="primary"
          isLoading={isLoading}
        />
      </div>

      {/* Menu Feedback */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-lg">🍽️</span>
          <span className="font-medium">Menu Feedback</span>
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
                style={{ width: `${(feedback.menu.good! / menuTotal) * 100}%` }}
              />
            </div>
            <span className="font-mono text-xs w-10 text-right">
              {feedback.menu.good}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs w-12 text-warning">OK</span>
            <div className="flex-1 h-6 bg-secondary rounded overflow-hidden">
              <div
                className="h-full bg-warning transition-all"
                style={{ width: `${(feedback.menu.ok! / menuTotal) * 100}%` }}
              />
            </div>
            <span className="font-mono text-xs w-10 text-right">
              {feedback.menu.ok}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs w-12 text-destructive">Bad</span>
            <div className="flex-1 h-6 bg-secondary rounded overflow-hidden">
              <div
                className="h-full bg-destructive transition-all"
                style={{ width: `${(feedback.menu.bad! / menuTotal) * 100}%` }}
              />
            </div>
            <span className="font-mono text-xs w-10 text-right">
              {feedback.menu.bad}
            </span>
          </div>
        </div>
      </div>

      {/* Workout Feedback */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-lg">💪</span>
          <span className="font-medium">Workout Feedback</span>
          <span className="ml-auto text-xs text-muted-foreground">
            {feedback.workout.users} users
          </span>
        </div>
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="p-3 rounded-lg bg-success/10 border border-success/20">
            <div className="text-xl font-bold text-success">
              {feedback.workout.strong}
            </div>
            <div className="text-xs text-muted-foreground">Strong</div>
          </div>
          <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
            <div className="text-xl font-bold text-primary">
              {feedback.workout.normal}
            </div>
            <div className="text-xs text-muted-foreground">Normal</div>
          </div>
          <div className="p-3 rounded-lg bg-warning/10 border border-warning/20">
            <div className="text-xl font-bold text-warning">
              {feedback.workout.tired}
            </div>
            <div className="text-xs text-muted-foreground">Tired</div>
          </div>
        </div>
      </div>

      {/* Top Loved Coach Messages */}
      <div className="stat-card">
        <div className="flex items-center gap-2 mb-4">
          <Heart className="h-4 w-4 text-destructive" />
          <span className="font-medium">Top Loved Coach Messages</span>
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
                <span className="font-mono text-sm">{msg.love}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Adaptation Engine */}
      <div className="border-t border-border pt-6">
        <div className="flex items-center gap-2 mb-4">
          <Settings2 className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">Adaptation Engine</h3>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <StatCard
            title="Adapted Users"
            value={adaptation.adapted_users}
            icon={Zap}
            variant="primary"
            isLoading={isLoading}
          />
          <StatCard
            title="Kcal Adjusted"
            value={adaptation.kcal_adjusted}
            icon={TrendingUp}
            isLoading={isLoading}
          />
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <StatCard
            title="Soft Mode"
            value={adaptation.soft_mode_users}
            isLoading={isLoading}
          />
          <StatCard
            title="Variant Switches"
            value={adaptation.variant_switches}
            isLoading={isLoading}
          />
        </div>

        {/* Validation Metrics */}
        <div className="stat-card">
          <span className="stat-label mb-4 block">Engine Validation</span>
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
            <span className="stat-label">Daily Adaptations (14d)</span>
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
