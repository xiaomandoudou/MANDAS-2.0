import { useMemo, useState } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { getStatusColor, getStatusIcon } from '@/lib/utils'

interface Step {
  step_id: number
  name: string
  description: string
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED'
  dependencies: number[]
  agent?: string
  start_time?: string
  end_time?: string
  started_at?: string
  completed_at?: string
  retry_count?: number
  result_preview?: string
  tool_name?: string
  tool_parameters?: any
}

interface DAGComponentProps {
  steps: Step[]
  onStepClick?: (stepId: number) => void
  onStepRightClick?: (stepId: number, event: React.MouseEvent) => void
}

const StepNode = ({ data }: { data: any }) => {
  const { step, onClick, onRightClick } = data
  const statusColor = getStatusColor(step.status)
  
  const getToolIcon = (toolName: string) => {
    const icons: Record<string, string> = {
      'file_reader': '📄',
      'code_runner': '⚙️',
      'text_summarizer': '📝',
      'web_scraper': '🌐',
      'shell_executor': '💻',
      'python_executor': '🐍',
      'default': '🔧'
    }
    return icons[toolName] || icons.default
  }
  
  return (
    <div
      className={`px-4 py-2 shadow-md rounded-md bg-white border-2 cursor-pointer hover:shadow-lg transition-shadow ${
        step.status === 'RUNNING' ? 'animate-pulse border-blue-500' : 
        step.status === 'FAILED' ? 'border-red-500 border-2' : 'border-gray-300'
      }`}
      onClick={() => onClick?.(step.step_id)}
      onContextMenu={(e) => {
        e.preventDefault()
        onRightClick?.(step.step_id, e)
      }}
    >
      <div className="flex items-center space-x-2">
        {step.tool_name && (
          <span className="text-lg">{getToolIcon(step.tool_name)}</span>
        )}
        <span className="text-lg">{getStatusIcon(step.status)}</span>
        <div>
          <div className="font-medium text-sm">{step.step_id}. {step.name}</div>
          <div className={`text-xs ${statusColor}`}>{step.status}</div>
          {step.status === 'RUNNING' && <div className="text-xs text-gray-500">运行中...</div>}
        </div>
      </div>
    </div>
  )
}

const nodeTypes = {
  stepNode: StepNode,
}

const StepDetailModal = ({ step, isOpen, onClose }: { step: Step | null; isOpen: boolean; onClose: () => void }) => {
  if (!isOpen || !step) return null
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <h3 className="text-lg font-semibold mb-4">步骤详情</h3>
        <div className="space-y-3">
          <div><strong>描述:</strong> {step.description}</div>
          {step.tool_name && <div><strong>工具:</strong> {step.tool_name}</div>}
          {step.tool_parameters && (
            <div>
              <strong>参数:</strong> 
              <pre className="mt-1 p-2 bg-gray-100 rounded text-sm overflow-x-auto">
                {JSON.stringify(step.tool_parameters, null, 2)}
              </pre>
            </div>
          )}
          {step.started_at && <div><strong>开始时间:</strong> {step.started_at}</div>}
          {step.completed_at && <div><strong>完成时间:</strong> {step.completed_at}</div>}
          {step.retry_count && step.retry_count > 0 && (
            <div><strong>重试次数:</strong> {step.retry_count}</div>
          )}
          {step.result_preview && (
            <div>
              <strong>结果预览:</strong>
              <div className="mt-1 p-2 bg-gray-100 rounded text-sm">
                {step.result_preview}
              </div>
            </div>
          )}
        </div>
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  )
}

export default function DAGComponent({ steps, onStepClick, onStepRightClick }: DAGComponentProps) {
  const [selectedStep, setSelectedStep] = useState<Step | null>(null)
  const [showModal, setShowModal] = useState(false)
  
  const handleStepClick = (stepId: number) => {
    const step = steps.find(s => s.step_id === stepId)
    if (step) {
      setSelectedStep(step)
      setShowModal(true)
    }
    onStepClick?.(stepId)
  }
  
  const handleStepRightClick = (stepId: number, event: React.MouseEvent) => {
    onStepRightClick?.(stepId, event)
  }

  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = steps.map((step, index) => ({
      id: step.step_id.toString(),
      type: 'stepNode',
      position: { x: (index % 3) * 200, y: Math.floor(index / 3) * 100 },
      data: { 
        step, 
        onClick: handleStepClick,
        onRightClick: handleStepRightClick
      },
    }))

    const edges: Edge[] = []
    steps.forEach((step) => {
      step.dependencies.forEach((depId) => {
        edges.push({
          id: `${depId}-${step.step_id}`,
          source: depId.toString(),
          target: step.step_id.toString(),
          animated: step.status === 'RUNNING',
        })
      })
    })

    return { nodes, edges }
  }, [steps])

  return (
    <>
      <div className="h-96 w-full border rounded-lg">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Controls />
          <Background />
          <MiniMap />
        </ReactFlow>
      </div>
      
      <StepDetailModal 
        step={selectedStep}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
      />
    </>
  )
}
