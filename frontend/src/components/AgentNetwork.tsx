import React, { useEffect, useState } from "react"
import {
  Server,
  Cloud,
  Activity,
  Globe,
  GitBranch,
  Workflow,
  ShieldCheck,
  BrainCircuit
} from "lucide-react"

interface AgentNetworkProps {
  activeAgent?: string | null
}

const agents = [
  { name: "K8s_Specialist", label: "Kubernetes", icon: Server, color: "text-blue-400", border: "border-blue-500", shadow: "shadow-[0_0_15px_rgba(59,130,246,0.5)]" },
  { name: "GCP_Specialist", label: "Google Cloud", icon: Cloud, color: "text-red-400", border: "border-red-500", shadow: "shadow-[0_0_15px_rgba(239,68,68,0.5)]" },
  { name: "Datadog_Specialist", label: "Datadog", icon: Activity, color: "text-purple-400", border: "border-purple-500", shadow: "shadow-[0_0_15px_rgba(168,85,247,0.5)]" },
  { name: "Azion_Specialist", label: "Azion Edge", icon: Globe, color: "text-orange-400", border: "border-orange-500", shadow: "shadow-[0_0_15px_rgba(249,115,22,0.5)]" },
  { name: "Git_Specialist", label: "Git / Repo", icon: GitBranch, color: "text-slate-200", border: "border-slate-500", shadow: "shadow-[0_0_15px_rgba(100,116,139,0.5)]" },
  { name: "CICD_Specialist", label: "CI/CD", icon: Workflow, color: "text-green-400", border: "border-green-500", shadow: "shadow-[0_0_15px_rgba(34,197,94,0.5)]" },
  { name: "Security_Specialist", label: "Security", icon: ShieldCheck, color: "text-yellow-400", border: "border-yellow-500", shadow: "shadow-[0_0_15px_rgba(234,179,8,0.5)]" },
]

export function AgentNetwork({ activeAgent }: AgentNetworkProps) {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  // We arrange agents in a circle
  const radius = 120 // px
  const center = 150 // px (half of container size 300)

  return (
    <div className="relative w-full h-[300px] flex items-center justify-center rounded-xl overflow-hidden mb-2">
      {/* Background Grid Effect */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:24px_24px]" />

      {/* Connecting Lines */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        <defs>
          <radialGradient id="grad1" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
            <stop offset="0%" style={{ stopColor: "rgba(59, 130, 246, 0.2)" }} />
            <stop offset="100%" style={{ stopColor: "rgba(0, 0, 0, 0)" }} />
          </radialGradient>
        </defs>
        <circle cx="50%" cy="50%" r="100" fill="url(#grad1)" />

        {agents.map((agent, index) => {
          const angle = (index * (360 / agents.length)) * (Math.PI / 180) - (Math.PI / 2)
          const x = center + radius * Math.cos(angle)
          const y = center + radius * Math.sin(angle)
          const isActive = activeAgent === agent.name
          const centerOffsetX = isClient && window.innerWidth < 500 ? 0 : 0

          return (
            <g key={`line-${agent.name}`}>
               <line
                 x1="50%"
                 y1="50%"
                 x2={`calc(50% + ${radius * Math.cos(angle)}px)`}
                 y2={`calc(50% + ${radius * Math.sin(angle)}px)`}
                 stroke={isActive ? "rgba(34, 211, 238, 0.8)" : "rgba(255, 255, 255, 0.1)"}
                 strokeWidth={isActive ? "2" : "1"}
                 strokeDasharray={isActive ? "4" : "0"}
                 className={`transition-all duration-500 ${isActive ? 'animate-pulse' : ''}`}
               />
            </g>
          )
        })}
      </svg>

      {/* Central Supervisor Node */}
      <div className="absolute z-20 flex flex-col items-center justify-center">
        <div className={`
          relative flex items-center justify-center w-16 h-16 rounded-full border-4 bg-black/50 backdrop-blur z-10 transition-all duration-500
          ${activeAgent === 'Supervisor' || !activeAgent ? 'border-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.6)]' : 'border-white/20'}
        `}>
          <BrainCircuit className={`w-8 h-8 ${activeAgent === 'Supervisor' || !activeAgent ? 'text-blue-400 animate-pulse' : 'text-white/50'}`} />
          {/* Ripple effect */}
          {(activeAgent === 'Supervisor' || !activeAgent) && (
             <div className="absolute inset-0 rounded-full border-2 border-blue-500 animate-ping opacity-20" />
          )}
        </div>
        <span className="mt-2 text-[10px] font-mono font-bold text-blue-300 bg-black/80 px-2 py-0.5 rounded">SUPERVISOR</span>
      </div>

      {/* Specialist Nodes */}
      {agents.map((agent, index) => {
        const angle = (index * (360 / agents.length)) * (Math.PI / 180) - (Math.PI / 2)
        // Position relative to center
        // We use style transform to position them
        const x = Math.cos(angle) * radius
        const y = Math.sin(angle) * radius

        const isActive = activeAgent === agent.name

        return (
          <div
            key={agent.name}
            className="absolute z-20 flex flex-col items-center justify-center transition-all duration-500"
            style={{
              transform: `translate(${x}px, ${y}px)`
            }}
          >
            <div className={`
              relative flex items-center justify-center w-10 h-10 rounded-full border-2 bg-black/50 backdrop-blur transition-all duration-300
              ${isActive ? `${agent.border} ${agent.shadow} scale-110` : 'border-white/20 grayscale opacity-60'}
            `}>
              <agent.icon className={`w-5 h-5 ${isActive ? agent.color : 'text-white/50'}`} />
              {isActive && (
                <div className={`absolute inset-0 rounded-full border ${agent.border} animate-ping opacity-30`} />
              )}
            </div>
            <span className={`
              mt-1 text-[9px] font-mono font-bold bg-black/80 px-1.5 py-0.5 rounded transition-colors whitespace-nowrap
              ${isActive ? agent.color : 'text-white/50'}
            `}>
              {agent.label}
            </span>
          </div>
        )
      })}
    </div>
  )
}
