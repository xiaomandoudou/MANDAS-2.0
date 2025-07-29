import { useParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { ArrowLeft, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { taskApi } from '@/lib/api'
import { formatDate, getStatusColor, getStatusText } from '@/lib/utils'
import { Link } from 'react-router-dom'
import DAGComponent from '@/components/DAGComponent'
import LogViewerComponent from '@/components/LogViewerComponent'
import ToolListComponent from '@/components/ToolListComponent'
import PlanningView from '@/components/PlanningView'
import { useWebSocket } from '@/hooks/useWebSocket'

export default function TaskDetailPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const [logs, setLogs] = useState<any[]>([])
  const [autoScroll, setAutoScroll] = useState(true)
  const queryClient = useQueryClient()

  const { data: task, isLoading, error } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => taskApi.get(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query?.state?.data?.data?.status
      return status === 'RUNNING' || status === 'QUEUED' ? 2000 : false
    },
  })

  const { connected } = useWebSocket({
    taskId: taskId || '',
    onStepUpdate: (update) => {
      console.log('Step update:', update)
    },
    onLogEntry: (log) => {
      setLogs(prev => [...prev, {
        id: `${Date.now()}-${Math.random()}`,
        ...log,
        timestamp: log.timestamp || new Date().toISOString()
      }])
    },
    onTaskEnd: (result) => {
      console.log('Task completed:', result)
    }
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'QUEUED':
        return <Clock className="h-5 w-5" />
      case 'RUNNING':
        return <Loader2 className="h-5 w-5 animate-spin" />
      case 'COMPLETED':
        return <CheckCircle className="h-5 w-5" />
      case 'FAILED':
        return <XCircle className="h-5 w-5" />
      default:
        return <Clock className="h-5 w-5" />
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-6 py-8">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </div>
    )
  }

  if (error || !task?.data) {
    return (
      <div className="container mx-auto px-6 py-8">
        <div className="text-center py-12">
          <XCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">任务未找到</h2>
          <p className="text-muted-foreground mb-4">请检查任务ID是否正确</p>
          <Link to="/">
            <Button>返回主页</Button>
          </Link>
        </div>
      </div>
    )
  }

  const taskData = task.data

  return (
    <div className="container mx-auto px-6 py-8">
      <div className="mb-6">
        <Link to="/">
          <Button variant="ghost" className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回主页
          </Button>
        </Link>
        
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">任务详情</h1>
          <div className={`flex items-center space-x-2 ${getStatusColor(taskData.status)}`}>
            {getStatusIcon(taskData.status)}
            <span className="font-medium">{getStatusText(taskData.status)}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8">
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">概览</TabsTrigger>
            <TabsTrigger value="dag">执行流程</TabsTrigger>
            <TabsTrigger value="logs">实时日志</TabsTrigger>
            <TabsTrigger value="tools">工具管理</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>任务描述</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground leading-relaxed">{taskData.prompt}</p>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                {taskData.result && (
                  <Card>
                    <CardHeader>
                      <CardTitle>执行结果</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {taskData.result.summary && (
                          <div>
                            <h4 className="font-medium mb-2">总结</h4>
                            <p className="text-sm text-muted-foreground leading-relaxed">
                              {taskData.result.summary}
                            </p>
                          </div>
                        )}
                        
                        {taskData.result.conversation && (
                          <div>
                            <h4 className="font-medium mb-2">对话记录</h4>
                            <div className="space-y-2 max-h-96 overflow-y-auto">
                              {taskData.result.conversation.map((msg: any, index: number) => (
                                <div key={index} className="p-3 rounded-lg bg-muted">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <span className="text-xs font-medium text-primary">
                                      {msg.name}
                                    </span>
                                    <span className="text-xs text-muted-foreground">
                                      ({msg.role})
                                    </span>
                                  </div>
                                  <p className="text-sm">{msg.content}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
              
              <div>
                <Card>
                  <CardHeader>
                    <CardTitle>任务信息</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">任务ID</label>
                      <p className="text-sm font-mono">{taskData.id}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">状态</label>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(taskData.status)}
                        <span className={`text-sm font-medium ${getStatusColor(taskData.status)}`}>
                          {getStatusText(taskData.status)}
                        </span>
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">WebSocket</label>
                      <div className="flex items-center space-x-2">
                        <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                        <span className="text-sm">{connected ? '已连接' : '未连接'}</span>
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">创建时间</label>
                      <p className="text-sm">{formatDate(taskData.created_at)}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">更新时间</label>
                      <p className="text-sm">{formatDate(taskData.updated_at)}</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="dag" className="space-y-6">
            <PlanningView 
              taskId={taskId!}
              plan={taskData.plan}
              onPlanRegenerate={() => {
                queryClient.invalidateQueries({ queryKey: ['task', taskId] })
              }}
            />
            
            <Card>
              <CardHeader>
                <CardTitle>DAG 执行流程</CardTitle>
              </CardHeader>
              <CardContent>
                {taskData.plan && taskData.plan.length > 0 ? (
                  <DAGComponent 
                    steps={taskData.plan.map((step: any, index: number) => ({
                      step_id: index + 1,
                      name: typeof step === 'string' ? `step_${index + 1}` : step.name || `step_${index + 1}`,
                      description: typeof step === 'string' ? step : step.description || step.name || '执行步骤',
                      status: taskData.status === 'COMPLETED' ? 'COMPLETED' : 
                              taskData.status === 'FAILED' ? 'FAILED' :
                              taskData.status === 'RUNNING' && index === 0 ? 'RUNNING' : 'QUEUED',
                      dependencies: index > 0 ? [index] : [],
                      agent: step.agent || 'unknown',
                      tool_name: step.tool_name,
                      tool_parameters: step.tool_parameters,
                      started_at: step.started_at,
                      completed_at: step.completed_at,
                      retry_count: step.retry_count || 0,
                      result_preview: step.result_preview
                    }))} 
                    onStepClick={(stepId) => {
                      console.log('Selected step:', stepId)
                    }}
                    onStepRightClick={(stepId) => {
                      console.log('Step right clicked:', stepId)
                    }}
                  />
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    暂无执行计划
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="logs" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>实时日志</CardTitle>
              </CardHeader>
              <CardContent>
                <LogViewerComponent 
                  logs={logs}
                  autoScroll={autoScroll}
                  onAutoScrollChange={setAutoScroll}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="tools" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>工具管理</CardTitle>
              </CardHeader>
              <CardContent>
                <ToolListComponent />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
