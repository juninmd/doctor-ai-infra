import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { MermaidDiagram } from './MermaidDiagram';
import { cn } from '../lib/utils';

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        code({ inline, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || '');
          const language = match ? match[1] : '';

          if (!inline && language === 'mermaid') {
            return <MermaidDiagram chart={String(children).replace(/\n$/, '')} />;
          }

          return !inline && match ? (
            <div className="relative my-4 rounded-lg overflow-hidden border border-white/10 bg-black/30">
                <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/10">
                    <span className="text-xs font-mono text-white/50">{language}</span>
                </div>
                <pre className={cn("p-4 overflow-x-auto text-sm", className)} {...props}>
                  <code className={className}>
                    {children}
                  </code>
                </pre>
            </div>
          ) : (
            <code className={cn("bg-white/10 rounded px-1.5 py-0.5 text-sm font-mono text-blue-200", className)} {...props}>
              {children}
            </code>
          );
        },
        p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
        ul: ({ children }) => <ul className="list-disc pl-4 mb-4 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-4 mb-4 space-y-1">{children}</ol>,
        li: ({ children }) => <li className="pl-1">{children}</li>,
        h1: ({ children }) => <h1 className="text-xl font-bold mb-4 mt-6 text-white">{children}</h1>,
        h2: ({ children }) => <h2 className="text-lg font-bold mb-3 mt-5 text-white">{children}</h2>,
        h3: ({ children }) => <h3 className="text-md font-bold mb-2 mt-4 text-white">{children}</h3>,
        a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 underline underline-offset-4">
                {children}
            </a>
        ),
        blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-blue-500/50 pl-4 italic text-white/70 my-4 bg-blue-500/5 py-2 rounded-r">
                {children}
            </blockquote>
        ),
        table: ({ children }) => (
            <div className="overflow-x-auto my-4 border border-white/10 rounded-lg">
                <table className="w-full text-sm text-left">{children}</table>
            </div>
        ),
        thead: ({ children }) => <thead className="bg-white/5 text-white/70 uppercase">{children}</thead>,
        th: ({ children }) => <th className="px-6 py-3 font-medium">{children}</th>,
        td: ({ children }) => <td className="px-6 py-4 border-t border-white/5">{children}</td>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
