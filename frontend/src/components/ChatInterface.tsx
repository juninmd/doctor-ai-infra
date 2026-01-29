import { useState, useRef, useEffect } from 'react';
import { Send, Terminal, Cpu, ShieldCheck, Activity } from 'lucide-react';
import { GlassCard } from './GlassCard';
import { ThinkingProcess, type AgentStep } from './ThinkingProcess';
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
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, steps]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsProcessing(true);
    setSteps([]);

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          history: messages.map(m => ({ role: m.role, content: m.content }))
        })
      });

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
                // Mark previous step as completed
                if (newSteps.length > 0) {
                    newSteps[newSteps.length - 1].status = 'completed';
                }
                // Add new step
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
                // If the last message is from the same agent, append to it (optional, but cleaner)
                // However, for this multi-agent setup, we usually want distinct blocks.
                // Let's just append for now.
                return [...prev, {
                    role: 'assistant',
                    content: event.content,
                    agent: event.agent
                }];
              });
            } else if (event.type === 'final') {
               setSteps(prev => {
                 return prev.map(s => ({ ...s, status: 'completed' }));
               });
               setIsProcessing(false);
            }
          } catch (err) {
            console.error("Error parsing JSON line:", line, err);
          }
        }
      }
    } catch (error) {
      console.error("Error calling chat:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Error communicating with the agent system." }]);
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col h-[85vh] max-w-5xl mx-auto w-full">
      {/* Header */}
      <GlassCard className="mb-6 flex items-center gap-4 py-4">
        <div className="p-3 rounded-xl bg-blue-500/20 border border-blue-500/30">
          <Terminal className="w-6 h-6 text-blue-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-200 to-indigo-400">
            SRE Intelligent Agent
          </h1>
          <p className="text-sm text-white/50">
            Autonomous Infrastructure Troubleshooting & Orchestration
          </p>
        </div>
        <div className="ml-auto flex gap-2">
            <Badge icon={Cpu} label="v2.0" />
            <Badge icon={ShieldCheck} label="Secure" />
            <Badge icon={Activity} label="Active" color="green" />
        </div>
      </GlassCard>

      {/* Main Chat Area */}
      <GlassCard className="flex-1 overflow-hidden flex flex-col relative !p-0">
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
                        "max-w-[80%] rounded-2xl p-4 text-sm leading-relaxed",
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
        </div>
      </GlassCard>
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
