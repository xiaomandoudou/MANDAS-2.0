import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'

interface Tool {
  name: string
  description: string
  category: string
  version: string
  author: string
  enabled: boolean
  parameters: any
  required_permissions: string[]
}

export default function ToolListComponent() {
  const [searchTerm, setSearchTerm] = useState('')

  const { data: toolsData, isLoading } = useQuery({
    queryKey: ['tools'],
    queryFn: () => api.get('/tools'),
  })

  const tools: Tool[] = toolsData?.data?.tools || []

  const filteredTools = tools.filter(tool =>
    tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tool.description.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (isLoading) {
    return <div>加载工具列表...</div>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-4">
        <Input
          placeholder="搜索工具..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
        <div className="text-sm text-gray-500">
          共 {tools.length} 个工具，{tools.filter(t => t.enabled).length} 个已启用
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTools.map((tool) => (
          <Card key={tool.name} className={tool.enabled ? '' : 'opacity-60'}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{tool.name}</CardTitle>
                <Badge variant={tool.enabled ? 'default' : 'secondary'}>
                  {tool.enabled ? '已启用' : '已禁用'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-3">{tool.description}</p>
              
              <div className="space-y-2 text-xs">
                <div><strong>分类:</strong> {tool.category}</div>
                <div><strong>版本:</strong> {tool.version}</div>
                <div><strong>作者:</strong> {tool.author}</div>
                
                {tool.required_permissions.length > 0 && (
                  <div>
                    <strong>所需权限:</strong>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {tool.required_permissions.map(perm => (
                        <Badge key={perm} variant="outline" className="text-xs">
                          {perm}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
