import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, RefreshCw, AlertCircle } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface PlanningViewProps {
  taskId: string
  plan?: any
  onPlanRegenerate?: () => void
}

const ErrorBanner = ({ error, onRetry }: { error: string; onRetry: () => void }) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
    <div className="flex items-center space-x-2">
      <AlertCircle className="h-5 w-5 text-red-500" />
      <span className="text-red-700">{error}</span>
      <Button variant="outline" size="sm" onClick={onRetry}>
        重试
      </Button>
    </div>
  </div>
)

const InfoBox = ({ text }: { text: string }) => (
  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-blue-700">
    {text}
  </div>
)

export default function PlanningView({ taskId, plan, onPlanRegenerate }: PlanningViewProps) {
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  if (plan?.steps?.length === 0) {
    return <InfoBox text="任务无需规划，直接进入执行阶段。" />
  }

  const handleRegenerate = async () => {
    setIsRegenerating(true)
    setError(null)
    
    try {
      const API_BASE_URL = (import.meta as any).env.VITE_API_URL || 'http://localhost:8081'
      const response = await fetch(`${API_BASE_URL}/mandas/v1/tasks/${taskId}/plan/regenerate`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) throw new Error('重新规划失败')
      
      const result = await response.json()
      toast({ 
        title: '重新规划成功', 
        description: `计划版本: ${result.plan_version}` 
      })
      onPlanRegenerate?.()
      
    } catch (err: any) {
      setError(err.message)
      toast({ 
        title: '重新规划失败', 
        description: err.message, 
        variant: 'destructive' 
      })
    } finally {
      setIsRegenerating(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>规划摘要</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRegenerate}
            disabled={isRegenerating}
          >
            {isRegenerating ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            重新规划
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {error && <ErrorBanner error={error} onRetry={handleRegenerate} />}
        <p className="text-foreground leading-relaxed">
          {plan?.summary || "好的，为了完成您的任务，我将分步执行计划中的各个步骤。"}
        </p>
      </CardContent>
    </Card>
  )
}
