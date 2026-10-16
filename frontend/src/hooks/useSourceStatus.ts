import { useEffect, useState } from 'react'

import { fetchSourceStatus, type SourceStatus } from '@/services/sourceClient'

export function useSourceStatus() {
  const [status, setStatus] = useState<SourceStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSourceStatus()
      .then(setStatus)
      .catch((err: Error) => setError(err.message))
  }, [])

  return { status, error }
}
