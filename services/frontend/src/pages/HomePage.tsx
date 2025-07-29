import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, Paperclip, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { taskApi, type Task } from '@/lib/api'
import { formatDate, getStatusColor, getStatusText } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { Link } from 'react-router-dom'

export default function HomePage() {
  const [prompt, setPrompt] = useState('')
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: tasksData, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => taskApi.list({ limit: 10 }),
  })

  const createTaskMutation = useMutation({
    mutationFn: taskApi.create,
    onSuccess: () => {
      toast({
        title: '任务创建成功',
        description: '任务已提交，正在处理中...',
      })
      setPrompt('')
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
    onError: (error: any) => {
      toast({
        title: '任务创建失败',
        description: error.response?.data?.detail || '请稍后重试',
        variant: 'destructive',
      })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim()) return
    
    createTaskMutation.mutate({
      prompt: prompt.trim(),
      config: { priority: 5 }
    })
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'QUEUED':
        return <Clock className="h-4 w-4" />
      case 'RUNNING':
        return <Loader2 className="h-4 w-4 animate-spin" />
      case 'COMPLETED':
        return <CheckCircle className="h-4 w-4" />
      case 'FAILED':
        return <XCircle className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  return (
    <div className="container mx-auto px-6 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>智能任务助手</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="flex space-x-2">
                  <Button type="button" variant="outline" size="icon">
                    <Paperclip className="h-4 w-4" />
                  </Button>
                  <Input
                    placeholder="请描述您需要完成的任务..."
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    className="flex-1"
                    disabled={createTaskMutation.isPending}
                  />
                  <Button 
                    type="submit" 
                    disabled={!prompt.trim() || createTaskMutation.isPending}
                  >
                    {createTaskMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground">
                  例如：分析这份销售报告并生成总结，编写一个Python脚本处理数据，或者回答技术问题等。
                </p>
              </form>
            </CardContent>
          </Card>

          <div className="mt-8">
            <h2 className="text-2xl font-bold mb-4">对话历史</h2>
            <div className="space-y-4">
              <Card>
                <CardContent className="p-6">
                  <div className="text-center text-muted-foreground">
                    <p>开始您的第一个任务对话</p>
                    <p className="text-sm mt-2">在上方输入框中描述您的需求，AI助手将为您提供帮助。</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle>任务历史</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : (
                <div className="space-y-3">
                  {tasksData?.data?.items?.map((task: Task) => (
                    <Link
                      key={task.id}
                      to={`/tasks/${task.id}`}
                      className="block p-3 rounded-lg border hover:bg-accent transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">
                            {task.prompt}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {formatDate(task.created_at)}
                          </p>
                        </div>
                        <div className={`flex items-center space-x-1 ml-2 ${getStatusColor(task.status)}`}>
                          {getStatusIcon(task.status)}
                          <span className="text-xs">{getStatusText(task.status)}</span>
                        </div>
                      </div>
                    </Link>
                  ))}
                  
                  {(!tasksData?.data?.items || tasksData.data.items.length === 0) && (
                    <div className="text-center text-muted-foreground py-8">
                      <p>暂无任务历史</p>
                      <p className="text-sm mt-2">创建您的第一个任务开始使用</p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
