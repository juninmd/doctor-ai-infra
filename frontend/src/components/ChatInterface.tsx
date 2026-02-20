import { useState, useRef, useEffect } from 'react';
import { Send, Terminal, Cpu, ShieldCheck, Activity } from 'lucide-react';
import { GlassCard } from './GlassCard';
import { ThinkingProcess, type AgentStep } from './ThinkingProcess';
import { AgentDashboard, type SystemStatus } from './AgentDashboard';
import { MarkdownRenderer } from './MarkdownRenderer';
import { cn } from '../lib/utils';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  agent?: string;
}

export function ChatInterface() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | undefined>(undefined);
  const [threadId] = useState(() => crypto.randomUUID());
  const [isWaitingForApproval, setIsWaitingForApproval] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, steps]);

  useEffect(() => {
    // Auto-detect infrastructure status from agent messages
    if (messages.length > 0) {
        const lastMsg = messages[messages.length - 1];
        if (lastMsg.role === 'assistant') {
            // Look for hidden JSON block from scan_infrastructure
            const match = lastMsg.content.match(/```json\n({[\s\S]*?})\n```/);
            if (match && match[1]) {
                try {
                    const data = JSON.parse(match[1]);
                    // Validate minimal structure
                    if (data.k8s && data.gcp) {
                        setSystemStatus(data);
                    }
                } catch (e) {
                    console.debug("Failed to parse status JSON", e);
                }
            }
        }
    }
  }, [messages]);

  const sendMessage = async (userMsg: string) => {
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsProcessing(true);
    setSteps([]);

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          history: messages.map(m => ({ role: m.role, content: m.content })),
          thread_id: threadId
        })
      });

      await processStream(response);
    } catch (error) {
      console.error("Error calling chat:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Error communicating with the agent system." }]);
      setIsProcessing(false);
    }
  };

  const processStream = async (response: Response) => {
      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const event = JSON.parse(line);

            if (event.type === 'activity') {
              setSteps(prev => {
                const newSteps = [...prev];
                if (newSteps.length > 0) {
                    newSteps[newSteps.length - 1].status = 'completed';
                }
                newSteps.push({
                    agent: event.agent,
                    status: 'active',
                    timestamp: Date.now()
                });
                return newSteps;
              });
            } else if (event.type === 'tool_call') {
                setSteps(prev => {
                    const newSteps = [...prev];
                    const activeIndex = newSteps.length - 1;
                    if (activeIndex >= 0) {
                        const step = { ...newSteps[activeIndex] };
                        step.toolCalls = [...(step.toolCalls || []), { tool: event.tool, args: event.args }];
                        newSteps[activeIndex] = step;
                    }
                    return newSteps;
                });
            } else if (event.type === 'message') {
              setMessages(prev => {
                return [...prev, {
                    role: 'assistant',
                    content: event.content,
                    agent: event.agent
                }];
              });
            } else if (event.type === 'approval_required') {
                setIsWaitingForApproval(true);
                // Keep isProcessing=true or false?
                // If waiting for approval, we stop the "thinking" spinner maybe?
                setIsProcessing(false);
            } else if (event.type === 'final') {
               setSteps(prev => {
                 return prev.map(s => ({ ...s, status: 'completed' }));
               });
               if (!isWaitingForApproval) setIsProcessing(false);
            }
          } catch (err) {
            console.error("Error parsing JSON line:", line, err);
          }
        }
      }
  };

  const handleResume = async (action: 'approve' | 'deny') => {
      setIsWaitingForApproval(false);
      setIsProcessing(true);
      try {
          const response = await fetch('/chat/resume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                thread_id: threadId,
                action: action
            })
          });
          await processStream(response);
      } catch (error) {
          console.error("Error resuming chat:", error);
          setMessages(prev => [...prev, { role: 'assistant', content: "Error communicating with the agent system." }]);
          setIsProcessing(false);
      }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;
    const msg = input;
    setInput('');
    await sendMessage(msg);
  };

  const handleRefresh = async () => {
    if (isProcessing) return;
    await sendMessage("Scan infrastructure status");
  };

  return (
    <div className="flex flex-col h-[90vh] max-w-7xl mx-auto w-full p-2 md:p-6 gap-6">
      {/* Header */}
      <GlassCard className="flex items-center gap-4 py-4 px-6 shrink-0">
        <div className="p-3 rounded-xl bg-blue-500/20 border border-blue-500/30">
          <Terminal className="w-6 h-6 text-blue-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-200 to-indigo-400">
            Infra Manager 2026
          </h1>
          <p className="text-sm text-white/50">
            Next-Gen Autonomous Infrastructure Troubleshooting
          </p>
        </div>
        <div className="ml-auto flex gap-2">
            <Badge icon={Cpu} label="AI: Auto-Detect" />
            <Badge icon={ShieldCheck} label="Secure" />
            <Badge icon={Activity} label="Active" color="green" />
        </div>
      </GlassCard>

      {/* Content Grid */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 overflow-hidden min-h-0">

        {/* Main Chat Area (Left/Top) */}
        <GlassCard className="lg:col-span-2 flex flex-col relative !p-0 overflow-hidden h-full">
            <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-white/30 space-y-4">
                        <BotIcon className="w-16 h-16 opacity-20" />
                        <p>Ready to troubleshoot. Describe your incident.</p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div key={idx} className={cn("flex flex-col", msg.role === 'user' ? "items-end" : "items-start")}>
                        <div className={cn(
                            "max-w-[90%] rounded-2xl p-4 text-sm leading-relaxed",
                            msg.role === 'user'
                                ? "bg-blue-600/20 border border-blue-500/30 text-blue-100 rounded-tr-none"
                                : "bg-white/5 border border-white/10 text-gray-200 rounded-tl-none"
                        )}>
                            {msg.agent && (
                                <div className="text-xs font-bold text-indigo-400 mb-1 flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
                                    {msg.agent}
                                </div>
                            )}
                            <MarkdownRenderer content={msg.content} />
                        </div>
                    </div>
                ))}

                {/* Thinking Process Display */}
                <ThinkingProcess steps={steps} isProcessing={isProcessing} />

                <div ref={scrollRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-white/10 bg-black/20 backdrop-blur-md">
                {isWaitingForApproval ? (
                    <div className="flex items-center justify-between bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
                        <div className="text-yellow-200 font-medium flex items-center gap-2">
                            <ShieldCheck className="w-5 h-5" />
                            <span>Authorization Required: Execute Runbook?</span>
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={() => handleResume('deny')}
                                className="px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 font-medium transition-colors"
                            >
                                Deny
                            </button>
                            <button
                                onClick={() => handleResume('approve')}
                                className="px-4 py-2 rounded-lg bg-green-500/20 hover:bg-green-500/30 text-green-300 font-medium transition-colors"
                            >
                                Approve
                            </button>
                        </div>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="relative">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Describe the infrastructure issue..."
                            className="w-full bg-white/5 border border-white/10 rounded-xl py-4 pl-6 pr-14 text-white placeholder:text-white/20 focus:outline-none focus:border-blue-500/50 focus:bg-white/10 transition-all shadow-inner"
                            disabled={isProcessing}
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isProcessing}
                            className="absolute right-2 top-2 p-2 rounded-lg bg-blue-500/20 hover:bg-blue-500/40 text-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    </form>
                )}
            </div>
        </GlassCard>

        {/* Dashboard Area (Right/Bottom) */}
        <div className="hidden lg:block h-full overflow-hidden">
            <AgentDashboard steps={steps} systemStatus={systemStatus} onRefresh={handleRefresh} />
        </div>
      </div>
    </div>
  );
}

function Badge({ icon: Icon, label, color = "blue" }: { icon: React.ElementType, label: string, color?: string }) {
    return (
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border bg-${color}-500/10 border-${color}-500/20 text-${color}-300 text-xs font-medium`}>
            <Icon className="w-3.5 h-3.5" />
            <span>{label}</span>
        </div>
    )
}

function BotIcon({ className }: { className?: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            <rect width="18" height="18" x="3" y="3" rx="2" />
            <path d="M9 3v18" />
            <path d="M15 3v18" />
            <path d="M9 9h6" />
            <path d="M9 15h6" />
        </svg>
    )
}
