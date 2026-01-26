
"use client"

import React, { useEffect, useState } from "react"
import {
  Server,
  Cloud,
  Activity,
  Globe,
  GitBranch,
  Workflow,
  ShieldCheck,
  BrainCircuit,
  Cpu
} from "lucide-react"

interface AgentNetworkProps {
  activeAgent?: string | null
}

const agents = [
  { name: "K8s_Specialist", label: "Kubernetes", icon: Server, color: "text-blue-400", border: "border-blue-500", shadow: "shadow-blue-500/50" },
  { name: "GCP_Specialist", label: "Google Cloud", icon: Cloud, color: "text-red-400", border: "border-red-500", shadow: "shadow-red-500/50" },
  { name: "Datadog_Specialist", label: "Datadog", icon: Activity, color: "text-purple-400", border: "border-purple-500", shadow: "shadow-purple-500/50" },
  { name: "Azion_Specialist", label: "Azion Edge", icon: Globe, color: "text-orange-400", border: "border-orange-500", shadow: "shadow-orange-500/50" },
  { name: "Git_Specialist", label: "Git / Repo", icon: GitBranch, color: "text-slate-200", border: "border-slate-500", shadow: "shadow-slate-500/50" },
  { name: "CICD_Specialist", label: "CI/CD", icon: Workflow, color: "text-green-400", border: "border-green-500", shadow: "shadow-green-500/50" },
  { name: "Security_Specialist", label: "Security", icon: ShieldCheck, color: "text-yellow-400", border: "border-yellow-500", shadow: "shadow-yellow-500/50" },
]

export function AgentNetwork({ activeAgent }: AgentNetworkProps) {
  // We arrange agents in a circle
  const radius = 140 // px
  const center = 180 // px (half of container size 360)

  return (
    <div className="relative w-full h-[400px] flex items-center justify-center bg-slate-950 rounded-xl border border-slate-800 overflow-hidden mb-6">
      {/* Background Grid Effect */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f2937_1px,transparent_1px),linear-gradient(to_bottom,#1f2937_1px,transparent_1px)] bg-[size:24px_24px] opacity-20" />

      {/* Connecting Lines */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        <defs>
          <radialGradient id="grad1" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
            <stop offset="0%" style={{ stopColor: "rgb(59 130 246)", stopOpacity: 0.1 }} />
            <stop offset="100%" style={{ stopColor: "rgb(2 6 23)", stopOpacity: 0 }} />
          </radialGradient>
        </defs>
        <circle cx="50%" cy="50%" r="100" fill="url(#grad1)" />

        {agents.map((agent, index) => {
          const angle = (index * (360 / agents.length)) * (Math.PI / 180) - (Math.PI / 2)
          const x = center + radius * Math.cos(angle)
          const y = center + radius * Math.sin(angle)
          const isActive = activeAgent === agent.name

          return (
            <g key={`line-${agent.name}`}>
               <line
                 x1="50%"
                 y1="50%"
                 x2={x + (window.innerWidth < 500 ? 0 : 0)} // simplified centering logic
                 y2={y}
                 stroke={isActive ? "cyan" : "#334155"}
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
          relative flex items-center justify-center w-20 h-20 rounded-full border-4 bg-slate-900 z-10 transition-all duration-500
          ${activeAgent === 'Supervisor' || !activeAgent ? 'border-blue-500 shadow-[0_0_30px_rgba(59,130,246,0.6)]' : 'border-slate-700'}
        `}>
          <BrainCircuit className={`w-10 h-10 ${activeAgent === 'Supervisor' || !activeAgent ? 'text-blue-400 animate-pulse' : 'text-slate-600'}`} />
          {/* Ripple effect */}
          {(activeAgent === 'Supervisor' || !activeAgent) && (
             <div className="absolute inset-0 rounded-full border-2 border-blue-500 animate-ping opacity-20" />
          )}
        </div>
        <span className="mt-2 text-xs font-mono font-bold text-blue-300 bg-slate-900/80 px-2 py-0.5 rounded">SUPERVISOR</span>
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
              relative flex items-center justify-center w-12 h-12 rounded-full border-2 bg-slate-900 transition-all duration-300
              ${isActive ? `${agent.border} ${agent.shadow} scale-110` : 'border-slate-700 grayscale opacity-70'}
            `}>
              <agent.icon className={`w-6 h-6 ${isActive ? agent.color : 'text-slate-500'}`} />
              {isActive && (
                <div className={`absolute inset-0 rounded-full border ${agent.border} animate-ping opacity-30`} />
              )}
            </div>
            <span className={`
              mt-1 text-[10px] font-mono font-bold bg-slate-900/80 px-1.5 py-0.5 rounded transition-colors
              ${isActive ? agent.color : 'text-slate-600'}
            `}>
              {agent.label}
            </span>
          </div>
        )
      })}

      {/* Activity Indicator */}
      <div className="absolute bottom-4 right-4 flex items-center gap-2">
         <div className={`w-2 h-2 rounded-full ${activeAgent ? 'bg-green-500 animate-pulse' : 'bg-slate-700'}`} />
         <span className="text-[10px] text-slate-500 font-mono uppercase">
           {activeAgent ? `PROCESSING: ${activeAgent.replace('_Specialist', '').toUpperCase()}` : 'IDLE'}
         </span>
      </div>
    </div>
  )
}
