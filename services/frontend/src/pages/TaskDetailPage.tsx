import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { taskApi } from '@/lib/api'
import { formatDate, getStatusColor, getStatusText } from '@/lib/utils'
import { Link } from 'react-router-dom'

export default function TaskDetailPage() {
  const { taskId } = useParams<{ taskId: string }>()

  const { data: task, isLoading, error } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => taskApi.get(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query?.state?.data?.data?.status
      return status === 'RUNNING' || status === 'QUEUED' ? 2000 : false
    },
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>任务描述</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-foreground leading-relaxed">{taskData.prompt}</p>
            </CardContent>
          </Card>

          {taskData.plan && taskData.plan.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>执行计划</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {taskData.plan.map((step: any, index: number) => (
                    <div key={index} className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center font-medium">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm">{step.description || step}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

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

          {taskData.status === 'FAILED' && taskData.result?.error && (
            <Card className="border-destructive">
              <CardHeader>
                <CardTitle className="text-destructive">错误信息</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-destructive">{taskData.result.error}</p>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
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
                <label className="text-sm font-medium text-muted-foreground">创建时间</label>
                <p className="text-sm">{formatDate(taskData.created_at)}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">更新时间</label>
                <p className="text-sm">{formatDate(taskData.updated_at)}</p>
              </div>
            </CardContent>
          </Card>

          {(taskData.status === 'RUNNING' || taskData.status === 'QUEUED') && (
            <Card>
              <CardHeader>
                <CardTitle>实时日志</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto font-mono text-xs">
                  <p className="text-muted-foreground">
                    [{formatDate(taskData.created_at)}] 任务已创建
                  </p>
                  {taskData.status === 'RUNNING' && (
                    <p className="text-blue-500">
                      [{formatDate(taskData.updated_at)}] 任务执行中...
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
