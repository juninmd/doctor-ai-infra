import { Activity, Terminal, RefreshCw, Zap } from 'lucide-react';
import { GlassCard } from './GlassCard';
import type { AgentStep } from './ThinkingProcess';
import { AgentNetwork } from './AgentNetwork';

export type MetricStatus = 'healthy' | 'warning' | 'error' | 'critical' | 'unknown';

export interface SystemStatus {
    timestamp: string;
    k8s: { status: MetricStatus; msg: string };
    gcp: { status: MetricStatus; msg: string };
    gmp: { status: MetricStatus; msg: string };
    datadog: { status: MetricStatus; msg: string };
    azion: { status: MetricStatus; msg: string };
    ai_insight?: string;
}

interface AgentDashboardProps {
    steps: AgentStep[];
    systemStatus?: SystemStatus;
    onRefresh?: () => void;
}

export function AgentDashboard({ steps, systemStatus, onRefresh }: AgentDashboardProps) {
    const activeStep = steps.find(s => s.status === 'active');
    const activeAgent = activeStep?.agent || "Supervisor";

    // Default mock status if none provided
    const status: SystemStatus = systemStatus || {
        timestamp: "unknown",
        k8s: { status: 'unknown', msg: 'Not Scanned' },
        gcp: { status: 'unknown', msg: 'Not Scanned' },
        gmp: { status: 'unknown', msg: 'Not Scanned' },
        datadog: { status: 'unknown', msg: 'Not Scanned' },
        azion: { status: 'unknown', msg: 'Not Scanned' },
        ai_insight: undefined
    };

    return (
        <div className="flex flex-col gap-4 h-full">
             {status.ai_insight && (
                <GlassCard className="p-4 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border-indigo-500/20">
                    <h3 className="text-xs font-bold text-indigo-300 tracking-wider mb-2 flex items-center gap-2">
                        <Zap className="w-3 h-3" />
                        AI INSIGHT
                    </h3>
                    <p className="text-sm text-indigo-100/90 leading-relaxed font-medium">
                        {status.ai_insight}
                    </p>
                </GlassCard>
             )}

             <GlassCard className="p-4">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xs font-bold text-white/50 tracking-wider flex items-center gap-2">
                        <Activity className="w-3 h-3 text-blue-400" />
                        LIVE STATUS
                    </h3>
                    {onRefresh && (
                        <button
                            onClick={onRefresh}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/50 hover:text-white transition-colors"
                            title="Scan Infrastructure"
                        >
                            <RefreshCw className="w-3 h-3" />
                        </button>
                    )}
                </div>
                <div className="grid grid-cols-2 gap-3">
                    <StatusMetric label="K8s Clusters" value={status.k8s.msg} status={status.k8s.status} />
                    <StatusMetric label="GCP Status" value={status.gcp.msg} status={status.gcp.status} />
                    <StatusMetric label="Datadog" value={status.datadog.msg} status={status.datadog.status} />
                    <StatusMetric label="Azion Edge" value={status.azion.msg} status={status.azion.status} />
                </div>
             </GlassCard>

             <GlassCard className="flex-1 p-4 flex flex-col items-center">
                <h3 className="text-xs font-bold text-white/50 tracking-wider mb-2 flex items-center gap-2 self-start">
                    <Terminal className="w-3 h-3 text-purple-400" />
                    LANGGRAPH AGENT NETWORK
                </h3>
                <div className="w-full flex-1 flex items-center justify-center">
                    <AgentNetwork activeAgent={activeAgent} />
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
