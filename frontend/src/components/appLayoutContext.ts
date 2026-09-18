import { useOutletContext } from 'react-router-dom'

import type {
  HealthResponse,
  ModelInfo,
} from '../api/types'


export type AppLayoutContext = {
  health: HealthResponse | null
  models: ModelInfo[]
  loadingSystem: boolean
  systemError: string | null
  backendHealthy: boolean
}


export function useAppLayout() {
  return useOutletContext<AppLayoutContext>()
}
