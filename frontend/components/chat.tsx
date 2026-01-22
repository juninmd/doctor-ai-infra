"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Bot, User, Terminal, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

interface Message {
  role: "user" | "assistant"
  content: string
  thoughts?: Thought[]
}

interface Thought {
  type: "tool_call" | "tool_result" | "thought"
  content: string
  agent?: string
}

interface Step {
  type: string
  content?: string
  name?: string
  tool_calls?: ToolCall[]
}

interface ToolCall {
  name: string
  args: unknown
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = { role: "user", content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage.content,
          history: messages.map(m => ({ role: m.role, content: m.content })),
        }),
      })

      if (!response.ok) throw new Error("Failed to send message")

      const data = await response.json()

      // Parse steps to extract thoughts
      // We assume the last message is the final answer.
      // Everything between the last user message and the last message are "thoughts".
      const allSteps = data.steps || []
      const thoughts: Thought[] = []

      // We process steps carefully.
      // Typically, we want to see what happened AFTER the user's message.
      // We can count how many messages we sent (history + 1) and look at the suffix.
      const previousCount = messages.length + 1 // history + current user message
      // Note: Backend might return logic that doesn't strictly 1-to-1 map if it summarizes.
      // But LangGraph usually appends.

      const newSteps = allSteps.slice(previousCount)

      // The last one is the final answer (Assistant Message)
      const thoughtSteps = newSteps.slice(0, newSteps.length - 1)

      thoughtSteps.forEach((step: Step) => {
        // Identify type
        const type = step.type
        // LangChain serialization:
        // human, ai, tool, etc.

        const content = step.content || ""
        let agentName = "System"

        // Try to guess agent from content or metadata if available
        // In our setup, we didn't explicitly attach agent names to messages except via "name" field if set.
        if (step.name) agentName = step.name

        if (type === "ai") {
           // Check for tool calls
           if (step.tool_calls && step.tool_calls.length > 0) {
             step.tool_calls.forEach((tc: ToolCall) => {
               thoughts.push({
                 type: "tool_call",
                 content: `Calling tool: ${tc.name} with args: ${JSON.stringify(tc.args)}`,
                 agent: agentName
               })
             })
           } else {
             thoughts.push({
               type: "thought",
               content: content,
               agent: agentName
             })
           }
        } else if (type === "tool") {
           thoughts.push({
             type: "tool_result",
             content: `Result: ${content}`,
             agent: "Tool"
           })
        }
      })

      // Just in case the final answer logic is tricky (e.g. Supervisor returns FINISH but the text is in previous msg)
      // Our backend returns "response" field explicitly.

      const botMessage: Message = {
        role: "assistant",
        content: data.response,
        thoughts: thoughts.length > 0 ? thoughts : undefined
      }

      setMessages((prev) => [...prev, botMessage])
    } catch (error) {
      console.error(error)
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I encountered an error. Please try again." },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[80vh] w-full max-w-4xl mx-auto border rounded-xl overflow-hidden shadow-xl bg-background">
      <div className="bg-slate-900 text-white p-4 flex items-center gap-2">
        <Terminal className="w-5 h-5" />
        <h1 className="font-bold">Infra Agent Manager</h1>
      </div>

      <ScrollArea className="flex-1 p-4 bg-slate-50/50">
        <div className="space-y-6">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-3 ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role === "assistant" && (
                <Avatar className="w-8 h-8 mt-1">
                   <AvatarFallback className="bg-blue-600 text-white"><Bot size={16}/></AvatarFallback>
                </Avatar>
              )}

              <div className={`max-w-[80%] space-y-2`}>
                <div
                  className={`p-3 rounded-lg text-sm ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-white border shadow-sm text-slate-800"
                  }`}
                >
                  {msg.content}
                </div>

                {msg.thoughts && (
                  <Accordion type="single" collapsible className="w-full">
                    <AccordionItem value="item-1" className="border rounded-md bg-slate-100 px-3">
                      <AccordionTrigger className="text-xs text-slate-500 py-2">
                        View Process
                      </AccordionTrigger>
                      <AccordionContent className="text-xs text-slate-600 font-mono space-y-2">
                        {msg.thoughts.map((t, i) => (
                          <div key={i} className="border-b border-slate-200 last:border-0 pb-2 mb-2">
                            <span className="font-bold text-slate-700">[{t.agent || t.type}]</span>: {t.content}
                          </div>
                        ))}
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                )}
              </div>

              {msg.role === "user" && (
                <Avatar className="w-8 h-8 mt-1">
                   <AvatarFallback className="bg-slate-700 text-white"><User size={16}/></AvatarFallback>
                </Avatar>
              )}
            </div>
          ))}
          {isLoading && (
             <div className="flex gap-3 justify-start">
               <Avatar className="w-8 h-8 mt-1">
                  <AvatarFallback className="bg-blue-600 text-white"><Bot size={16}/></AvatarFallback>
               </Avatar>
               <div className="bg-white border shadow-sm p-3 rounded-lg flex items-center gap-2">
                 <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                 <span className="text-xs text-slate-500">Thinking...</span>
               </div>
             </div>
          )}
          <div ref={scrollRef} />
        </div>
      </ScrollArea>

      <div className="p-4 bg-white border-t">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your infrastructure issue..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button type="submit" disabled={isLoading} className="bg-blue-600 hover:bg-blue-700">
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </div>
  )
}
