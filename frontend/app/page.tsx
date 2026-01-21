
"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Send, Bot, User, Terminal } from "lucide-react"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"

interface Message {
  role: string
  content: string
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hey! I'm your Infra Manager. What's up with your stack today?" }
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [openItems, setOpenItems] = useState<Record<number, boolean>>({})
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo(0, scrollRef.current.scrollHeight)
    }
  }, [messages])

  const toggleAccordion = (index: number) => {
    setOpenItems(prev => ({ ...prev, [index]: !prev[index] }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage = { role: "user", content: input }
    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.content }),
      })

      if (!res.ok) throw new Error("Failed to fetch response")

      const data = await res.json()

      // Process history to separate thoughts from final response
      if (data.history && data.history.length > 0) {
           data.history.forEach((msg: any) => {
               // We only want to add agent actions/thoughts that are NOT the final user input (which we already added)
               // and NOT the final response (which we add at the end or if it's the last one)
               if (msg.role !== "user" && msg.content !== data.response) {
                    setMessages(prev => [...prev, { role: msg.role, content: msg.content }])
               }
           })
      }

      setMessages(prev => [...prev, { role: "assistant", content: data.response }])
    } catch (error) {
      console.error(error)
      setMessages(prev => [...prev, { role: "assistant", content: "My bad, something crashed. Check the logs." }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-indigo-50 to-blue-100 p-4 font-sans">
      <Card className="w-full max-w-4xl h-[85vh] flex flex-col shadow-2xl border-0 ring-1 ring-black/5 rounded-2xl overflow-hidden backdrop-blur-sm bg-white/90">
        <CardHeader className="border-b bg-white/80 backdrop-blur-md rounded-t-2xl py-5 px-8 sticky top-0 z-10">
          <CardTitle className="flex items-center gap-4 text-xl font-bold text-slate-800">
            <div className="bg-gradient-to-tr from-blue-600 to-indigo-600 p-2.5 rounded-xl shadow-lg shadow-blue-500/20">
                <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-700 to-indigo-700">
                Infra Agent Manager
              </span>
              <p className="text-xs font-normal text-slate-500 mt-0.5">Automated Infrastructure Troubleshooting</p>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 p-0 overflow-hidden flex flex-col bg-slate-50/50">
          <ScrollArea className="flex-1 p-6" ref={scrollRef}>
            <div className="space-y-8 pb-4">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex items-start gap-4 ${
                    msg.role === "user" ? "flex-row-reverse" : "flex-row"
                  }`}
                >
                  <Avatar className={msg.role === "user" ? "bg-gradient-to-tr from-blue-600 to-indigo-600 ring-4 ring-white shadow-md" : "bg-gradient-to-tr from-emerald-500 to-teal-600 ring-4 ring-white shadow-md"}>
                    <AvatarFallback className="text-white font-bold">
                      {msg.role === "user" ? <User size={18} /> : <Bot size={18} />}
                    </AvatarFallback>
                  </Avatar>

                  <div className={`flex flex-col max-w-[85%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                    <span className="text-xs text-slate-400 mb-1.5 font-medium uppercase tracking-wider ml-1">{msg.role}</span>

                    <div
                        className={`p-5 rounded-3xl shadow-sm transition-all duration-200 hover:shadow-md ${
                        msg.role === "user"
                            ? "bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-tr-sm shadow-blue-500/10"
                            : "bg-white text-slate-700 border border-slate-100 rounded-tl-sm shadow-slate-200/50"
                        }`}
                    >
                        {msg.role !== "user" && (msg.content.includes("Agent") || msg.role !== "assistant") ? (
                             <Accordion className="w-full min-w-[300px]" >
                                 <AccordionItem className="border-b-0">
                                     <AccordionTrigger
                                        open={!!openItems[index]}
                                        onToggle={() => toggleAccordion(index)}
                                        className="py-1 hover:no-underline text-xs text-slate-500 font-semibold group"
                                     >
                                        <div className="flex items-center gap-2 group-hover:text-blue-600 transition-colors">
                                            <div className="p-1 bg-slate-100 rounded-md group-hover:bg-blue-50">
                                                <Terminal size={12} className="text-slate-600 group-hover:text-blue-600"/>
                                            </div>
                                            Thought Process <span className="text-slate-300">|</span> <span className="uppercase text-[10px] tracking-wider">{msg.role}</span>
                                        </div>
                                     </AccordionTrigger>
                                     <AccordionContent open={!!openItems[index]} className="pt-3">
                                         <div className="bg-slate-900 text-emerald-400 p-4 rounded-xl font-mono text-xs overflow-x-auto shadow-inner border border-slate-800">
                                            {msg.content}
                                         </div>
                                     </AccordionContent>
                                 </AccordionItem>
                             </Accordion>
                        ) : (
                            <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                        )}
                    </div>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex items-center gap-4">
                   <Avatar className="bg-gradient-to-tr from-emerald-500 to-teal-600 ring-4 ring-white shadow-md">
                    <AvatarFallback className="text-white"><Bot size={18}/></AvatarFallback>
                  </Avatar>
                  <div className="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm rounded-tl-sm">
                    <div className="flex gap-2">
                      <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-bounce" />
                      <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-bounce delay-75" />
                      <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-bounce delay-150" />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          <div className="p-4 bg-white/80 backdrop-blur-md border-t px-6 py-5">
            <form onSubmit={handleSubmit} className="flex gap-3 relative">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Describe your infrastructure problem..."
                className="flex-1 h-14 pl-6 pr-4 bg-slate-50 border-slate-200 focus-visible:ring-blue-500 rounded-xl shadow-sm transition-all focus:bg-white focus:shadow-md text-base"
              />
              <Button type="submit" disabled={isLoading} className="h-14 w-14 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 p-0 shadow-lg shadow-blue-500/30 transition-all hover:scale-105 active:scale-95">
                <Send size={22} />
              </Button>
            </form>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
