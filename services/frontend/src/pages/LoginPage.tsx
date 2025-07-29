import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { LogIn, UserPlus, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { authApi } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import { useToast } from '@/hooks/use-toast'
import { useNavigate } from 'react-router-dom'

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
  })
  
  const { login } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()

  const loginMutation = useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      authApi.login(username, password),
    onSuccess: (data) => {
      login(data.data.access_token)
      toast({
        title: '登录成功',
        description: '欢迎使用 Mandas Agent System',
      })
      navigate('/')
    },
    onError: (error: any) => {
      toast({
        title: '登录失败',
        description: error.response?.data?.detail || '用户名或密码错误',
        variant: 'destructive',
      })
    },
  })

  const registerMutation = useMutation({
    mutationFn: ({ username, email, password }: { username: string; email: string; password: string }) =>
      authApi.register(username, email, password),
    onSuccess: (data) => {
      login(data.data.access_token)
      toast({
        title: '注册成功',
        description: '欢迎使用 Mandas Agent System',
      })
      navigate('/')
    },
    onError: (error: any) => {
      toast({
        title: '注册失败',
        description: error.response?.data?.detail || '注册失败，请稍后重试',
        variant: 'destructive',
      })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (isLogin) {
      loginMutation.mutate({
        username: formData.username,
        password: formData.password,
      })
    } else {
      registerMutation.mutate({
        username: formData.username,
        email: formData.email,
        password: formData.password,
      })
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const isLoading = loginMutation.isPending || registerMutation.isPending

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="h-12 w-12 rounded-lg bg-primary flex items-center justify-center mx-auto mb-4">
            <span className="text-primary-foreground font-bold text-lg">M</span>
          </div>
          <h1 className="text-2xl font-bold">Mandas Agent System</h1>
          <p className="text-muted-foreground mt-2">
            智能体系统 - 让AI为您工作
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-center">
              {isLogin ? '登录账户' : '创建账户'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="username" className="text-sm font-medium">
                  用户名
                </label>
                <Input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={formData.username}
                  onChange={handleInputChange}
                  disabled={isLoading}
                />
              </div>

              {!isLogin && (
                <div>
                  <label htmlFor="email" className="text-sm font-medium">
                    邮箱
                  </label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={handleInputChange}
                    disabled={isLoading}
                  />
                </div>
              )}

              <div>
                <label htmlFor="password" className="text-sm font-medium">
                  密码
                </label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  disabled={isLoading}
                />
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : isLogin ? (
                  <LogIn className="h-4 w-4 mr-2" />
                ) : (
                  <UserPlus className="h-4 w-4 mr-2" />
                )}
                {isLogin ? '登录' : '注册'}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <button
                type="button"
                onClick={() => setIsLogin(!isLogin)}
                className="text-sm text-primary hover:underline"
                disabled={isLoading}
              >
                {isLogin ? '没有账户？点击注册' : '已有账户？点击登录'}
              </button>
            </div>

            {isLogin && (
              <div className="mt-4 p-3 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground text-center">
                  演示账户：admin / admin123
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
