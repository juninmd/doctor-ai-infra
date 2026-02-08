import { Activity, Server, Cloud, Shield, GitBranch, Terminal } from 'lucide-react';
import { GlassCard } from './GlassCard';
import type { AgentStep } from './ThinkingProcess';
import { motion } from 'framer-motion';

export type MetricStatus = 'healthy' | 'warning' | 'error' | 'critical' | 'unknown';

export interface SystemStatus {
    timestamp: string;
    k8s: { status: MetricStatus; msg: string };
    gcp: { status: MetricStatus; msg: string };
    gmp: { status: MetricStatus; msg: string };
    datadog: { status: MetricStatus; msg: string };
    azion: { status: MetricStatus; msg: string };
}

interface AgentDashboardProps {
    steps: AgentStep[];
    systemStatus?: SystemStatus;
}

export function AgentDashboard({ steps, systemStatus }: AgentDashboardProps) {
    const activeStep = steps.find(s => s.status === 'active');
    const activeAgent = activeStep?.agent || "Supervisor";

    const agents = [
        { id: "K8s_Specialist", icon: Server, label: "Kubernetes" },
        { id: "GCP_Specialist", icon: Cloud, label: "Google Cloud" },
        { id: "Datadog_Specialist", icon: Activity, label: "Datadog" },
        { id: "Azion_Specialist", icon: Cloud, label: "Azion Edge" },
        { id: "Security_Specialist", icon: Shield, label: "Security" },
        { id: "Git_Specialist", icon: GitBranch, label: "Git/CI" },
    ];

    // Default mock status if none provided
    const status = systemStatus || {
        k8s: { status: 'unknown', msg: 'Not Scanned' },
        gcp: { status: 'unknown', msg: 'Not Scanned' },
        gmp: { status: 'unknown', msg: 'Not Scanned' },
        datadog: { status: 'unknown', msg: 'Not Scanned' },
        azion: { status: 'unknown', msg: 'Not Scanned' }
    };

    return (
        <div className="flex flex-col gap-4 h-full">
             <GlassCard className="p-4">
                <h3 className="text-xs font-bold text-white/50 tracking-wider mb-4 flex items-center gap-2">
                    <Activity className="w-3 h-3 text-blue-400" />
                    LIVE INFRASTRUCTURE STATUS
                </h3>
                <div className="grid grid-cols-2 gap-3">
                    <StatusMetric label="K8s Clusters" value={status.k8s.msg} status={status.k8s.status} />
                    <StatusMetric label="GCP Status" value={status.gcp.msg} status={status.gcp.status} />
                    <StatusMetric label="Datadog" value={status.datadog.msg} status={status.datadog.status} />
                    <StatusMetric label="Azion Edge" value={status.azion.msg} status={status.azion.status} />
                </div>
             </GlassCard>

             <GlassCard className="flex-1 p-4 overflow-y-auto">
                <h3 className="text-xs font-bold text-white/50 tracking-wider mb-4 flex items-center gap-2">
                    <Terminal className="w-3 h-3 text-purple-400" />
                    AGENT NEURAL NETWORK
                </h3>
                <div className="space-y-3">
                    {agents.map((agent) => {
                        const isActive = activeAgent === agent.id;
                        const hasActed = steps.some(s => s.agent === agent.id);

                        return (
                            <motion.div
                                key={agent.id}
                                animate={{
                                    scale: isActive ? 1.02 : 1,
                                    borderColor: isActive ? 'rgba(59, 130, 246, 0.5)' : 'rgba(255,255,255,0.05)'
                                }}
                                className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${
                                    isActive ? 'bg-blue-500/10 border-blue-500/30' :
                                    hasActed ? 'bg-white/5 border-white/10 opacity-100' : 'bg-transparent border-transparent opacity-40'
                                }`}
                            >
                                <div className={`p-2 rounded-lg ${isActive ? 'bg-blue-500/20 text-blue-300' : 'bg-white/5 text-white/50'}`}>
                                    <agent.icon className="w-4 h-4" />
                                </div>
                                <div>
                                    <div className={`text-sm font-medium ${isActive ? 'text-white' : 'text-white/70'}`}>
                                        {agent.label}
                                    </div>
                                    <div className="text-xs text-white/30">
                                        {isActive ? 'Processing...' : hasActed ? 'Standby' : 'Idle'}
                                    </div>
                                </div>
                                {isActive && (
                                    <div className="ml-auto w-2 h-2 rounded-full bg-blue-400 animate-pulse shadow-[0_0_10px_rgba(96,165,250,0.5)]" />
                                )}
                            </motion.div>
                        );
                    })}
                </div>
             </GlassCard>
        </div>
    );
}

function StatusMetric({ label, value, status }: { label: string, value: string, status: MetricStatus }) {
    const colors: Record<MetricStatus, string> = {
        healthy: 'text-green-400 border-green-500/20 bg-green-500/5',
        warning: 'text-yellow-400 border-yellow-500/20 bg-yellow-500/5',
        critical: 'text-red-400 border-red-500/20 bg-red-500/5',
        error: 'text-red-400 border-red-500/20 bg-red-500/5',
        unknown: 'text-gray-400 border-gray-500/20 bg-gray-500/5',
    };

    return (
        <div className={`p-3 rounded-lg border ${colors[status] || colors.unknown} flex flex-col justify-between`}>
            <div className="text-[10px] uppercase tracking-wider opacity-70 mb-1">{label}</div>
            <div className="font-mono text-sm font-bold">{value}</div>
        </div>
    );
}
