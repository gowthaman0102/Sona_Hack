import { useContext } from 'react'

import { AuraSessionContext } from './AuraSessionStore'


export function useAuraSession() {
  const context = useContext(AuraSessionContext)

  if (!context) {
    throw new Error(
      'useAuraSession must be used within AuraSessionProvider.',
    )
  }

  return context
}
