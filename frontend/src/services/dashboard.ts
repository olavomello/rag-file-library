import { apiGet, apiPatch, apiPostStream } from './apiClient';
import type {
  DashboardStats,
  ModelsResponse,
  ModelsStatus,
  SettingsUpdate,
  SettingsUpdateResponse,
  SettingsView,
} from '../types';

/** NDJSON events streamed by POST /models/pull while a model downloads. */
export type ModelPullEvent =
  | { type: 'progress'; status: string; completed: number | null; total: number | null }
  | { type: 'done' }
  | { type: 'error'; detail: string };

export function pullModel(model: string, signal?: AbortSignal): AsyncGenerator<ModelPullEvent> {
  return apiPostStream<ModelPullEvent>('/models/pull', { model }, signal);
}

export function fetchDashboardStats(signal?: AbortSignal): Promise<DashboardStats> {
  return apiGet<DashboardStats>('/dashboard/stats', signal);
}

export function fetchSettings(signal?: AbortSignal): Promise<SettingsView> {
  return apiGet<SettingsView>('/settings', signal);
}

export function fetchModelsStatus(signal?: AbortSignal): Promise<ModelsStatus> {
  return apiGet<ModelsStatus>('/models/status', signal);
}

export function fetchModels(signal?: AbortSignal): Promise<ModelsResponse> {
  return apiGet<ModelsResponse>('/models', signal);
}

export function updateSettings(patch: SettingsUpdate): Promise<SettingsUpdateResponse> {
  return apiPatch<SettingsUpdateResponse>('/settings', patch);
}
