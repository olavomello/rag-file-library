import { apiGet, apiPatch } from './apiClient';
import type {
  DashboardStats,
  ModelsStatus,
  SettingsUpdate,
  SettingsUpdateResponse,
  SettingsView,
} from '../types';

export function fetchDashboardStats(signal?: AbortSignal): Promise<DashboardStats> {
  return apiGet<DashboardStats>('/dashboard/stats', signal);
}

export function fetchSettings(signal?: AbortSignal): Promise<SettingsView> {
  return apiGet<SettingsView>('/settings', signal);
}

export function fetchModelsStatus(signal?: AbortSignal): Promise<ModelsStatus> {
  return apiGet<ModelsStatus>('/models/status', signal);
}

export function updateSettings(patch: SettingsUpdate): Promise<SettingsUpdateResponse> {
  return apiPatch<SettingsUpdateResponse>('/settings', patch);
}
