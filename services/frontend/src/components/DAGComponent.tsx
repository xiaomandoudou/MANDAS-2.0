import { useMemo } from 'react'
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
}

interface DAGComponentProps {
  steps: Step[]
  onStepClick?: (stepId: number) => void
}

const StepNode = ({ data }: { data: any }) => {
  const { step, onClick } = data
  const statusColor = getStatusColor(step.status)
  
  return (
    <div
      className={`px-4 py-2 shadow-md rounded-md bg-white border-2 cursor-pointer hover:shadow-lg transition-shadow ${
        step.status === 'RUNNING' ? 'animate-pulse border-blue-500' : 'border-gray-300'
      }`}
      onClick={() => onClick?.(step.step_id)}
    >
      <div className="flex items-center space-x-2">
        <span className="text-lg">{getStatusIcon(step.status)}</span>
        <div>
          <div className="font-medium text-sm">{step.step_id}. {step.name}</div>
          <div className={`text-xs ${statusColor}`}>{step.status}</div>
        </div>
      </div>
    </div>
  )
}

const nodeTypes = {
  stepNode: StepNode,
}

export default function DAGComponent({ steps, onStepClick }: DAGComponentProps) {
  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = steps.map((step, index) => ({
      id: step.step_id.toString(),
      type: 'stepNode',
      position: { x: (index % 3) * 200, y: Math.floor(index / 3) * 100 },
      data: { step, onClick: onStepClick },
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
  }, [steps, onStepClick])

  return (
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
  )
}
