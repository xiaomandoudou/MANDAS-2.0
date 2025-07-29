import { useEffect, useState } from 'react'

interface WebSocketHookProps {
  taskId: string
  onStepUpdate?: (update: any) => void
  onLogEntry?: (log: any) => void
  onTaskEnd?: (result: any) => void
  onPlanGenerated?: (plan: any) => void
}

export function useWebSocket({ taskId, onStepUpdate, onLogEntry, onTaskEnd, onPlanGenerated }: WebSocketHookProps) {
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    if (!taskId) return

    const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8081'
    const wsUrl = `${WS_BASE_URL}/mandas/v1/tasks/${taskId}/stream`
    let ws: WebSocket | null = null

    try {
      ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        setConnected(true)
        console.log('WebSocket connected for task:', taskId)
      }

      ws.onclose = () => {
        setConnected(false)
        console.log('WebSocket disconnected for task:', taskId)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'step_status_update') {
            onStepUpdate?.(data.payload)
          } else if (data.type === 'log') {
            onLogEntry?.(data.payload)
          } else if (data.type === 'task_end') {
            onTaskEnd?.(data.payload)
          } else if (data.type === 'plan_generated') {
            onPlanGenerated?.(data.payload)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnected(false)
      }

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setConnected(false)
    }

    return () => {
      if (ws) {
        ws.close()
      }
    }
  }, [taskId, onStepUpdate, onLogEntry, onTaskEnd])

  return { connected }
}
