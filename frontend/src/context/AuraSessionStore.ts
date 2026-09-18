import { createContext } from 'react'

import type {
  ModelTier,
  MultiTaskExecutionResult,
  QueryAnalysis,
  RoutedResponse,
} from '../api/types'


export type AuraSessionContextValue = {
  prompt: string
  setPrompt: (value: string) => void
  overrideTier: ModelTier | ''
  setOverrideTier: (value: ModelTier | '') => void
  analysis: QueryAnalysis | null
  setAnalysis: (value: QueryAnalysis | null) => void
  routeResult: RoutedResponse | null
  setRouteResult: (value: RoutedResponse | null) => void
  multiPrompt: string
  setMultiPrompt: (value: string) => void
  multiResult: MultiTaskExecutionResult | null
  setMultiResult: (value: MultiTaskExecutionResult | null) => void
}


export const AuraSessionContext = createContext<
  AuraSessionContextValue | undefined
>(undefined)


export const defaultRoutePrompt =
  'Explain how database indexing improves query performance.'

export const defaultMultiTaskPrompt =
  'Summarize why database indexes improve performance; extract the email alice@example.com; and explain when a full table scan may still be useful.'
