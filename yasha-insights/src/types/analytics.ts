export interface OverviewData {
  total_users: number;
  active_24h: number;
  active_7d: number;
  active_30d: number;
  free_users: number;
  trial_users: number;
  premium_users: number;
}

export interface CohortData {
  cohort_date: string;
  new_users: number;
  d1: number;
  d7: number;
  d30: number;
}

export interface RetentionData {
  d1_retention: number;
  d7_retention: number;
  d30_retention: number;
  cohorts: CohortData[];
}

export interface FeatureCost {
  feature: string;
  tokens: number;
  cost_usd: number;
}

export interface DailyCost {
  date: string;
  tokens: number;
  cost_usd: number;
}

export interface AICostsData {
  total_tokens: number;
  total_cost_usd: number;
  by_feature: FeatureCost[];
  daily: DailyCost[];
}

export interface FeedbackCategory {
  good?: number;
  ok?: number;
  bad?: number;
  strong?: number;
  normal?: number;
  tired?: number;
  like?: number;
  love?: number;
  meh?: number;
  users: number;
}

export interface TopLovedCoach {
  coach_msg_key: string;
  category: string;
  love: number;
}

export interface FeedbackData {
  menu: FeedbackCategory;
  workout: FeedbackCategory;
  coach: FeedbackCategory;
  top_loved_coach: TopLovedCoach[];
}

export interface AdaptationDaily {
  date: string;
  count: number;
}

export interface AdaptationValidation {
  menu_complaints: number;
  menu_fixed: number;
  workout_tired: number;
  soft_mode_applied: number;
}

export interface AdaptationData {
  adapted_users: number;
  kcal_adjusted: number;
  soft_mode_users: number;
  variant_switches: number;
  daily: AdaptationDaily[];
  validation: AdaptationValidation;
}

export interface AuthResponse {
  token: string;
  user?: {
    id: number;
    username?: string;
    first_name: string;
  };
}

export interface ApiError {
  detail: string;
  status: number;
}
