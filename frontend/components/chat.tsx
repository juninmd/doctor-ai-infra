"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Bot, User, Terminal, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { AgentNetwork } from "@/components/agent-network"

interface Message {
  role: "user" | "assistant"
  content: string
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [activeAgent, setActiveAgent] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages, activeAgent]) // Scroll on updates

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = { role: "user", content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    // Add placeholder for assistant
    setMessages((prev) => [...prev, { role: "assistant", content: "" }])

    try {
      const response = await fetch("/chat", { // Updated to match backend route
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage.content,
        }),
      })

      if (!response.ok || !response.body) throw new Error("Failed to send message")

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")

        // Keep the last possibly incomplete line in buffer
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (!line.trim()) continue
          try {
            const event = JSON.parse(line)

            if (event.type === "activity") {
              setActiveAgent(event.agent)
            } else if (event.type === "message") {
              // Append to last message
              const content = event.content
              const agentName = event.agent

              // We'll format the content to show who is speaking if it's not the final answer
              // Or just append it directly.
              // To make it look like a log: `[Agent]: message`

              setMessages((prev) => {
                const newMsgs = [...prev]
                const lastMsg = newMsgs[newMsgs.length - 1]

                let textToAppend = content
                if (agentName && agentName !== "Supervisor" && content.trim().length > 0) {
                   textToAppend = `**[${agentName.replace('_Specialist', '')}]**: ${content}\n\n`
                }

                lastMsg.content += textToAppend
                return newMsgs
              })
            } else if (event.type === "final") {
              setActiveAgent(null)
            }
          } catch (err) {
            console.error("Error parsing JSON chunk", err)
          }
        }
      }

    } catch (error) {
      console.error(error)
      setMessages((prev) => {
         const newMsgs = [...prev]
         const lastMsg = newMsgs[newMsgs.length - 1]
         lastMsg.content += "\n\n*Error: Failed to complete request.*"
         return newMsgs
      })
    } finally {
      setIsLoading(false)
      setActiveAgent(null)
    }
  }

  return (
    <div className="flex flex-col h-[90vh] w-full max-w-5xl mx-auto border border-slate-800 rounded-xl overflow-hidden shadow-2xl bg-slate-950 text-slate-100">
      <div className="bg-slate-900 border-b border-slate-800 p-4 flex items-center gap-2 shadow-lg z-10">
        <Terminal className="w-5 h-5 text-blue-500" />
        <h1 className="font-bold font-mono tracking-wider text-blue-400">INFRA_AGENT_NET // v2.0</h1>
      </div>

      <div className="flex-1 overflow-hidden relative flex flex-col">
        {/* Network Visualizer Overlay/Section */}
        <div className="w-full bg-slate-950/50 backdrop-blur-sm border-b border-slate-800 z-0">
          <AgentNetwork activeAgent={activeAgent} />
        </div>

        <ScrollArea className="flex-1 p-4">
          <div className="space-y-6 max-w-3xl mx-auto pb-4">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex gap-3 ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.role === "assistant" && (
                  <Avatar className="w-8 h-8 mt-1 border border-blue-500/50">
                     <AvatarFallback className="bg-slate-900 text-blue-400"><Bot size={16}/></AvatarFallback>
                  </Avatar>
                )}

                <div className={`max-w-[85%] space-y-2`}>
                  <div
                    className={`p-4 rounded-lg text-sm font-mono whitespace-pre-wrap ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white shadow-[0_0_15px_rgba(37,99,235,0.3)]"
                        : "bg-slate-900 border border-slate-800 text-slate-300 shadow-lg"
                    }`}
                  >
                    {msg.content}
                    {msg.role === "assistant" && isLoading && index === messages.length - 1 && (
                       <span className="inline-block w-2 h-4 ml-1 bg-blue-500 animate-pulse align-middle" />
                    )}
                  </div>
                </div>

                {msg.role === "user" && (
                  <Avatar className="w-8 h-8 mt-1 border border-slate-600">
                     <AvatarFallback className="bg-slate-800 text-slate-300"><User size={16}/></AvatarFallback>
                  </Avatar>
                )}
              </div>
            ))}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>
      </div>

      <div className="p-4 bg-slate-900 border-t border-slate-800">
        <form onSubmit={handleSubmit} className="flex gap-2 max-w-3xl mx-auto">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Initialize infrastructure analysis..."
            disabled={isLoading}
            className="flex-1 bg-slate-950 border-slate-700 text-slate-100 placeholder:text-slate-500 focus-visible:ring-blue-500"
          />
          <Button type="submit" disabled={isLoading} className="bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_10px_rgba(37,99,235,0.5)] transition-all">
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </Button>
        </form>
      </div>
    </div>
  )
}
