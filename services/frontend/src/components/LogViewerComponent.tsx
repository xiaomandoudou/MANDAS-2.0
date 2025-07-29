import { useState, useEffect, useRef } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { formatDate } from '@/lib/utils'

interface LogEntry {
  id: string
  level: 'INFO' | 'DEBUG' | 'WARN' | 'ERROR'
  message: string
  timestamp: string
  step_id?: number
  agent?: string
}

interface LogViewerProps {
  logs: LogEntry[]
  autoScroll?: boolean
  onAutoScrollChange?: (enabled: boolean) => void
}

export default function LogViewerComponent({ 
  logs, 
  autoScroll = true, 
  onAutoScrollChange 
}: LogViewerProps) {
  const [filter, setFilter] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('ALL')
  const scrollRef = useRef<HTMLDivElement>(null)

  const filteredLogs = logs.filter(log => {
    const matchesText = log.message.toLowerCase().includes(filter.toLowerCase())
    const matchesLevel = levelFilter === 'ALL' || log.level === levelFilter
    return matchesText && matchesLevel
  })




  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs, autoScroll])

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'bg-red-100 text-red-800'
      case 'WARN': return 'bg-yellow-100 text-yellow-800'
      case 'DEBUG': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="h-full flex flex-col space-y-4">
      <div className="flex items-center space-x-2">
        <Input
          placeholder="搜索日志..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="flex-1"
        />
        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          className="px-3 py-2 border rounded-md"
        >
          <option value="ALL">所有级别</option>
          <option value="ERROR">ERROR</option>
          <option value="WARN">WARN</option>
          <option value="INFO">INFO</option>
          <option value="DEBUG">DEBUG</option>
        </select>
      </div>

      <div className="flex items-center space-x-2">
        <Button
          variant={autoScroll ? "default" : "outline"}
          size="sm"
          onClick={() => onAutoScrollChange?.(!autoScroll)}
        >
          自动滚动
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            
          }}
        >
          清空日志
        </Button>
      </div>

      <ScrollArea className="flex-1 h-64" ref={scrollRef}>
        <div className="space-y-1 font-mono text-xs">
          {filteredLogs.map((log) => (
            <div key={log.id} className="flex items-start space-x-2 p-2 hover:bg-gray-50">
              <Badge className={getLevelColor(log.level)}>
                {log.level}
              </Badge>
              <div className="flex-1">
                <div className="flex items-center space-x-2 text-gray-500">
                  <span>{formatDate(log.timestamp)}</span>
                  {log.step_id && <span>Step {log.step_id}</span>}
                  {log.agent && <span>[{log.agent}]</span>}
                </div>
                <div className="mt-1">{log.message}</div>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
