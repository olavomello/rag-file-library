export type HealthStatusValue = 'ok' | 'unavailable' | 'error';

export interface LivenessResponse {
  status: string;
  app_name: string;
  app_env: string;
  version: string;
}

export interface ComponentHealthResponse {
  component: string;
  status: HealthStatusValue;
  detail: string | null;
  metadata: Record<string, string>;
}
