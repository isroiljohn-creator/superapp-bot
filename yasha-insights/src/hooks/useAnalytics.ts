import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type {
  OverviewData,
  RetentionData,
  AICostsData,
  FeedbackData,
  AdaptationData,
} from '@/types/analytics';

export function useOverview() {
  return useQuery<OverviewData>({
    queryKey: ['analytics', 'overview'],
    queryFn: () => api.getOverview(),
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 10000,
  });
}

export function useRetention(days: number = 30) {
  return useQuery<RetentionData>({
    queryKey: ['analytics', 'retention', days],
    queryFn: () => api.getRetention(days),
    refetchInterval: 60000,
    staleTime: 30000,
  });
}

export function useAICosts(range: string = '7d') {
  return useQuery<AICostsData>({
    queryKey: ['analytics', 'ai-costs', range],
    queryFn: () => api.getAICosts(range),
    refetchInterval: 60000,
    staleTime: 30000,
  });
}

export function useFeedback(range: string = '7d') {
  return useQuery<FeedbackData>({
    queryKey: ['analytics', 'feedback', range],
    queryFn: () => api.getFeedback(range),
    refetchInterval: 60000,
    staleTime: 30000,
  });
}

export function useAdaptation(range: string = '14d') {
  return useQuery<AdaptationData>({
    queryKey: ['analytics', 'adaptation', range],
    queryFn: () => api.getAdaptation(range),
    refetchInterval: 60000,
    staleTime: 30000,
  });
}

// New Hooks for Advanced Analytics tab
export function useGrowth() {
  return useQuery<{ data: { date: string; value: number }[] }>({
    queryKey: ['analytics', 'growth'],
    queryFn: () => api.getGrowth(),
    refetchInterval: 60000,
  });
}

export function useFunnel() {
  return useQuery<{ data: { name: string; value: number }[] }>({
    queryKey: ['analytics', 'funnel'],
    queryFn: () => api.getFunnelGraph(),
    refetchInterval: 60000,
  });
}

export function useRetentionGraph() {
  return useQuery<{ data: { name: string; value: number }[] }>({
    queryKey: ['analytics', 'retention_graph'],
    queryFn: () => api.getRetentionGraph(),
    refetchInterval: 60000,
  });
}

export function usePremiumDist() {
  return useQuery<{ data: { name: string; value: number }[] }>({
    queryKey: ['analytics', 'premium'],
    queryFn: () => api.getPremiumDist(),
    refetchInterval: 60000,
  });
}

// Mock data for development/demo
export const mockOverview: OverviewData = {
  total_users: 2847,
  active_24h: 342,
  active_7d: 1205,
  active_30d: 2156,
  free_users: 1823,
  trial_users: 412,
  premium_users: 612,
};

export const mockRetention: RetentionData = {
  d1_retention: 0.68,
  d7_retention: 0.42,
  d30_retention: 0.28,
  cohorts: [
    { cohort_date: '2025-12-01', new_users: 120, d1: 82, d7: 51, d30: 34 },
    { cohort_date: '2025-12-08', new_users: 145, d1: 98, d7: 62, d30: 0 },
    { cohort_date: '2025-12-15', new_users: 168, d1: 118, d7: 0, d30: 0 },
    { cohort_date: '2025-12-22', new_users: 134, d1: 89, d7: 0, d30: 0 },
  ],
};

export const mockAICosts: AICostsData = {
  total_tokens: 2450000,
  total_cost_usd: 147.32,
  by_feature: [
    { feature: 'menu', tokens: 980000, cost_usd: 58.80 },
    { feature: 'workout', tokens: 720000, cost_usd: 43.20 },
    { feature: 'coach', tokens: 750000, cost_usd: 45.32 },
  ],
  daily: [
    { date: '2025-12-21', tokens: 320000, cost_usd: 19.20 },
    { date: '2025-12-22', tokens: 345000, cost_usd: 20.70 },
    { date: '2025-12-23', tokens: 380000, cost_usd: 22.80 },
    { date: '2025-12-24', tokens: 290000, cost_usd: 17.40 },
    { date: '2025-12-25', tokens: 420000, cost_usd: 25.20 },
    { date: '2025-12-26', tokens: 385000, cost_usd: 23.10 },
    { date: '2025-12-27', tokens: 310000, cost_usd: 18.92 },
  ],
};

export const mockFeedback: FeedbackData = {
  menu: { good: 856, ok: 423, bad: 87, users: 1366 },
  workout: { strong: 542, normal: 678, tired: 234, users: 1454 },
  coach: { like: 423, love: 312, meh: 156, users: 891 },
  top_loved_coach: [
    { coach_msg_key: 'GENTLE_NUDGE_01', category: 'GENTLE_NUDGE', love: 89 },
    { coach_msg_key: 'MOTIVATION_03', category: 'MOTIVATION', love: 76 },
    { coach_msg_key: 'CELEBRATION_02', category: 'CELEBRATION', love: 68 },
  ],
};

export const mockAdaptation: AdaptationData = {
  adapted_users: 423,
  kcal_adjusted: 287,
  soft_mode_users: 156,
  variant_switches: 89,
  daily: [
    { date: '2025-12-13', count: 28 },
    { date: '2025-12-14', count: 32 },
    { date: '2025-12-15', count: 25 },
    { date: '2025-12-16', count: 38 },
    { date: '2025-12-17', count: 42 },
    { date: '2025-12-18', count: 35 },
    { date: '2025-12-19', count: 29 },
    { date: '2025-12-20', count: 31 },
    { date: '2025-12-21', count: 44 },
    { date: '2025-12-22', count: 38 },
    { date: '2025-12-23', count: 27 },
    { date: '2025-12-24', count: 19 },
    { date: '2025-12-25', count: 22 },
    { date: '2025-12-26', count: 33 },
  ],
  validation: {
    menu_complaints: 87,
    menu_fixed: 72,
    workout_tired: 234,
    soft_mode_applied: 156,
  },
};
