import {
  useState,
  type ReactNode,
} from 'react'

import {
  AuraSessionContext,
  defaultMultiTaskPrompt,
  defaultRoutePrompt,
} from './AuraSessionStore'
import type {
  ModelTier,
  MultiTaskExecutionResult,
  QueryAnalysis,
  RoutedResponse,
} from '../api/types'


export default function AuraSessionProvider({
  children,
}: {
  children: ReactNode
}) {
  const [prompt, setPrompt] = useState(defaultRoutePrompt)
  const [overrideTier, setOverrideTier] =
    useState<ModelTier | ''>('')
  const [analysis, setAnalysis] =
    useState<QueryAnalysis | null>(null)
  const [routeResult, setRouteResult] =
    useState<RoutedResponse | null>(null)
  const [multiPrompt, setMultiPrompt] =
    useState(defaultMultiTaskPrompt)
  const [multiResult, setMultiResult] =
    useState<MultiTaskExecutionResult | null>(null)

  return (
    <AuraSessionContext.Provider
      value={{
        prompt,
        setPrompt,
        overrideTier,
        setOverrideTier,
        analysis,
        setAnalysis,
        routeResult,
        setRouteResult,
        multiPrompt,
        setMultiPrompt,
        multiResult,
        setMultiResult,
      }}
    >
      {children}
    </AuraSessionContext.Provider>
  )
}
