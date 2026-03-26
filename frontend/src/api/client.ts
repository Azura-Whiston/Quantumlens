import axios from 'axios';
import type { SimulationRequest, SimulationResponse, HardwareInfo, PresetCircuit, NaturalLanguageResponse } from '../types/quantum';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

export async function simulate(request: SimulationRequest): Promise<SimulationResponse> {
  const { data } = await api.post<SimulationResponse>('/simulate', request);
  return data;
}

export async function getHardware(): Promise<HardwareInfo> {
  const { data } = await api.get<HardwareInfo>('/hardware');
  return data;
}

export async function getPresets(): Promise<PresetCircuit[]> {
  const { data } = await api.get<PresetCircuit[]>('/presets');
  return data;
}

export async function naturalLanguageSimulate(
  prompt: string,
  sessionId?: string,
): Promise<NaturalLanguageResponse> {
  const { data } = await api.post<NaturalLanguageResponse>('/simulate/natural', {
    prompt,
    session_id: sessionId,
  });
  return data;
}

export async function healthCheck(): Promise<boolean> {
  try {
    const { data } = await api.get('/health');
    return data.status === 'ok';
  } catch {
    return false;
  }
}
