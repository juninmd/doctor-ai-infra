import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, Bot, ArrowRight, CheckCircle2, Loader2 } from 'lucide-react';
import { cn } from '../lib/utils';

export interface AgentStep {
  agent: string;
  status: 'pending' | 'active' | 'completed';
  timestamp: number;
}

interface ThinkingProcessProps {
  steps: AgentStep[];
  isProcessing: boolean;
}

export function ThinkingProcess({ steps, isProcessing }: ThinkingProcessProps) {
  const [isOpen, setIsOpen] = useState(true);

  // Auto-expand when new steps arrive if processing
  useEffect(() => {
    if (isProcessing && steps.length > 0) {
      setIsOpen(true);
    }
  }, [steps.length, isProcessing]);

  if (steps.length === 0 && !isProcessing) return null;

  return (
    <div className="w-full max-w-3xl mx-auto mb-4">
      <div
        className={cn(
          "rounded-xl overflow-hidden border border-white/10 transition-all duration-300",
          isOpen ? "bg-black/20" : "bg-black/10 hover:bg-black/20 cursor-pointer"
        )}
      >
        <div
          className="flex items-center justify-between p-3 px-4"
          onClick={() => setIsOpen(!isOpen)}
        >
          <div className="flex items-center gap-2 text-sm font-medium text-blue-200">
            {isProcessing ? (
              <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
            ) : (
              <Bot className="w-4 h-4 text-blue-400" />
            )}
            <span>
              {isProcessing ? "Orchestrating Agents..." : "Orchestration Complete"}
            </span>
            <span className="text-xs text-white/40 ml-2">
              ({steps.length} steps)
            </span>
          </div>
          <button className="text-white/40 hover:text-white/80 transition-colors">
            {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="p-4 pt-0 space-y-3">
                <div className="h-px w-full bg-white/5 mb-3" />

                {steps.map((step, index) => (
                  <motion.div
                    key={`${step.agent}-${index}`}
                    initial={{ x: -10, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center gap-3 text-sm"
                  >
                    <div className={cn(
                      "flex items-center justify-center w-6 h-6 rounded-full border",
                      step.status === 'active'
                        ? "border-blue-500 bg-blue-500/20 text-blue-300 animate-pulse"
                        : "border-white/10 bg-white/5 text-white/40"
                    )}>
                      {step.status === 'active' ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <CheckCircle2 className="w-3 h-3 text-green-400" />
                      )}
                    </div>

                    <div className="flex flex-col">
                      <span className={cn(
                        "font-medium",
                        step.status === 'active' ? "text-blue-300" : "text-gray-300"
                      )}>
                        {step.agent.replace('_', ' ')}
                      </span>
                    </div>

                    {index < steps.length - 1 && (
                      <ArrowRight className="w-3 h-3 text-white/20 ml-auto" />
                    )}
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
