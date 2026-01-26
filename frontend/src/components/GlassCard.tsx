import React from 'react';
import { cn } from '../lib/utils';
import { motion } from 'framer-motion';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
}

export function GlassCard({ children, className, hoverEffect = false, ...props }: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={cn(
        "glass-panel rounded-2xl p-6",
        hoverEffect && "hover:bg-white/10 transition-colors duration-300",
        className
      )}
      {...props as any}
    >
      {children}
    </motion.div>
  );
}
