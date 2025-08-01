"use client"

import { useState, useRef, useEffect, KeyboardEvent } from "react"
import { Send, Mic, Paperclip, Loader2, BrainCircuit } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ProcessStepsRenderer, ProcessStep } from "@/components/ProcessStepsRenderer"

// 核心Message接口保持不变
interface Message {
  id: number | string;
  isUser: boolean;
  timestamp: Date;
  content: string;
  isThinking: boolean;
  processSteps: ProcessStep[];
}

export default function ChatApp() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      content: "你好！我是Hive AI助手。我已经准备就绪，随时可以处理您的复杂任务。",
      isUser: false,
      timestamp: new Date(Date.now() - 300000),
      isThinking: false,
      processSteps: [],
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const isAgentThinking = messages[messages.length - 1]?.isThinking || false;

  useEffect(() => {
    chatContainerRef.current?.scrollTo({
      top: chatContainerRef.current.scrollHeight,
      behavior: 'smooth'
    });
  }, [messages]);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const scrollHeight = textarea.scrollHeight;
      textarea.style.height = `${Math.min(scrollHeight, 128)}px`;
    }
  }, [inputValue]);

  const callHiveStreamAPI = (userMessage: string, history: Message[]) => {
    const userMessageId = Date.now();
    const agentMessageId = `agent_${userMessageId}`;
    
    const newUserMessage: Message = {
      id: userMessageId, content: userMessage, isUser: true, timestamp: new Date(),
      isThinking: false, processSteps: []
    };
    
    const newAgentMessage: Message = {
      id: agentMessageId, content: "", isUser: false, timestamp: new Date(),
      isThinking: true, processSteps: []
    };
    
    setMessages(prev => [...prev, newUserMessage, newAgentMessage]);

    const graphInputMessages = history
      .filter(msg => !msg.content.startsWith("你好！"))
      .map(msg => ({ role: msg.isUser ? "human" : "ai", content: msg.content }));
    graphInputMessages.push({ role: "human", content: userMessage });

    const requestBody = { input: { messages: graphInputMessages } };

    // --- 【核心修改】: 分别读取Host和Port，然后拼接URL ---
    const apiHost = process.env.NEXT_PUBLIC_API_HOST || "http://localhost";
    const apiPort = process.env.NEXT_PUBLIC_API_PORT || "8000";
    const apiBaseUrl = `${apiHost}:${apiPort}`;
    const eventUrl = `${apiBaseUrl}/nexus/stream_events`;
    // ---------------------------------------------------
    
    console.log(`Connecting to backend at: ${eventUrl}`); // 增加日志，方便调试

    fetch(eventUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
      body: JSON.stringify(requestBody),
    }).then(response => {
        if (!response.ok) throw new Error(`服务器响应错误: ${response.status}`);
        if (!response.body) throw new Error("响应体为空");
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        function push() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    setMessages(prev => prev.map(msg => 
                        msg.id === agentMessageId ? { ...msg, isThinking: false } : msg
                    ));
                    return;
                }
                
                const rawChunks = decoder.decode(value, { stream: true }).split('\n\n');
                
                rawChunks.forEach(rawChunk => {
                    if (!rawChunk.startsWith('data:')) return;
                    const dataString = rawChunk.substring(5).trim();
                    if (dataString === '[DONE]') return;

                    try {
                        const chunk = JSON.parse(dataString);
                        const { event, data, run_id, name: nodeName } = chunk;

                        setMessages(prevMessages => prevMessages.map(msg => {
                            if (msg.id !== agentMessageId) return msg;

                            const updatedMsg = { ...msg, processSteps: [...msg.processSteps] };

                            switch (event) {
                                case 'on_chain_start':
                                    if (nodeName === 'agent') {
                                        const lastStep = updatedMsg.processSteps[updatedMsg.processSteps.length - 1];
                                        if (lastStep?.type === 'TOOL_CALL' && lastStep?.status === 'done') {
                                            updatedMsg.processSteps.push({
                                                id: run_id, type: 'PLANNING',
                                                title: 'Nexus 核心 - 正在评估工具结果...', status: 'running',
                                            });
                                        } else if (!updatedMsg.processSteps.some(s => s.type === 'PLANNING')) {
                                            updatedMsg.processSteps.push({
                                                id: run_id, type: 'PLANNING',
                                                title: 'Nexus 核心 - 正在分析需求与规划...', status: 'running',
                                            });
                                        }
                                    }
                                    break;

                                case 'on_tool_start':
                                    const toolInput = data.input?.args || data.input || {};
                                    const toolName = nodeName.charAt(0).toUpperCase() + nodeName.slice(1);
                                    let toolTitle = `调用工具: [${toolName}]`;
                                    if (toolInput.query) toolTitle = `调用 [${toolName}] - 研究: "${toolInput.query.slice(0, 30)}..."`;
                                    else if (toolInput.expression) toolTitle = `调用 [${toolName}] - 计算: "${toolInput.expression}"`;
                                    else if (toolInput.operation) toolTitle = `调用 [${toolName}] - 文件操作: ${toolInput.operation}`;

                                    const planningStepIndex = updatedMsg.processSteps.findIndex(s => s.type === 'PLANNING' && s.status === 'running');
                                    if(planningStepIndex !== -1) {
                                        const newSteps = [...updatedMsg.processSteps];
                                        newSteps[planningStepIndex] = { ...newSteps[planningStepIndex], status: 'done' };
                                        updatedMsg.processSteps = newSteps;
                                    }

                                    updatedMsg.processSteps.push({
                                        id: run_id, type: 'TOOL_CALL', title: toolTitle,
                                        content: { tool_input: data.input }, status: 'running',
                                    });
                                    break;
                                
                                case 'on_tool_end':
                                    const toolStepIndex = updatedMsg.processSteps.findIndex(s => s.id === run_id);
                                    if (toolStepIndex !== -1) {
                                        const newSteps = [...updatedMsg.processSteps];
                                        let parsedOutput;
                                        try { parsedOutput = JSON.parse(data.output); } catch { parsedOutput = data.output; }
                                        newSteps[toolStepIndex] = { ...newSteps[toolStepIndex], status: 'done', content: { ...newSteps[toolStepIndex].content, tool_output: parsedOutput } };
                                        updatedMsg.processSteps = newSteps;
                                    }
                                    break;
                                
                                case 'on_chat_model_stream':
                                    if (nodeName === 'agent' && data?.chunk?.content) {
                                        const finalPlanningStepIndex = updatedMsg.processSteps.findIndex(s => s.type === 'PLANNING' && s.status === 'running');
                                        if (finalPlanningStepIndex !== -1) {
                                            const newSteps = [...updatedMsg.processSteps];
                                            newSteps[finalPlanningStepIndex] = { ...newSteps[finalPlanningStepIndex], status: 'done', title: 'Nexus 核心 - 生成最终回复' };
                                            updatedMsg.processSteps = newSteps;
                                        }
                                        updatedMsg.content += data.chunk.content;
                                    }
                                    break;
                            }
                            return updatedMsg;
                        }));

                    } catch (error) {
                         console.error("解析SSE事件数据失败:", dataString, error);
                    }
                });
                push();
            }).catch(err => {
                 console.error("读取数据流时发生错误:", err);
                 setMessages(prev => prev.map(msg => 
                    msg.id === agentMessageId ? { ...msg, content: "抱歉，读取数据流时发生错误。", isThinking: false } : msg
                ));
            });
        }
        push();
    }).catch(err => {
        console.error("API调用失败:", err);
        setMessages(prev => prev.map(msg => 
          msg.id === agentMessageId ? { ...msg, content: `抱歉，与Hive的连接失败了: ${err.message}`, isThinking: false } : msg
        ));
    });
  };

  const handleSendMessage = () => {
    if (inputValue.trim() && !isAgentThinking) {
      callHiveStreamAPI(inputValue.trim(), messages);
      setInputValue("");
    }
  };
  
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        handleSendMessage();
    }
  };

  const formatTime = (date: Date) => new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="h-screen w-full relative overflow-hidden bg-gradient-to-br from-gray-50 via-slate-100 to-gray-200">
       <div className="absolute inset-0 opacity-20"><div className="absolute top-20 left-20 w-72 h-72 bg-gray-300 rounded-full mix-blend-multiply filter blur-xl animate-pulse"></div><div className="absolute top-40 right-20 w-72 h-72 bg-slate-300 rounded-full mix-blend-multiply filter blur-xl animate-pulse delay-1000"></div><div className="absolute bottom-20 left-1/2 w-72 h-72 bg-gray-400 rounded-full mix-blend-multiply filter blur-xl animate-pulse delay-2000"></div></div>
      <div className="relative h-full flex flex-col">
        <div className="backdrop-blur-xl bg-white/30 border-b border-gray-200/30 px-8 py-4"><div className="flex items-center justify-between"><div className="flex items-center space-x-3"><div className="w-3 h-3 bg-red-400 rounded-full"></div><div className="w-3 h-3 bg-yellow-400 rounded-full"></div><div className="w-3 h-3 bg-green-400 rounded-full"></div></div><div className="flex items-center space-x-2"><BrainCircuit className="h-5 w-5 text-purple-600" /><h1 className="text-lg font-medium text-slate-700">Hive</h1>{isAgentThinking && <Loader2 className="h-4 w-4 animate-spin text-purple-500" />}</div><div className="w-16"></div></div></div>
        
        <div ref={chatContainerRef} className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.isUser ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-4xl ${message.isUser ? "ml-12" : "mr-12"}`}>
                <div className={`backdrop-blur-md rounded-2xl shadow-lg ${message.isUser ? "bg-blue-500/80 text-white ml-auto shadow-blue-500/20" : "bg-white/60 text-slate-700 border border-white/30 shadow-gray-500/20"}`}>
                  
                  {message.content && (
                    <div className="px-4 py-3">
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                    </div>
                  )}

                  {message.processSteps.length > 0 && (
                     <div className={`px-4 py-3 ${message.content ? 'border-t border-black/10' : ''}`}>
                       <ProcessStepsRenderer steps={message.processSteps} />
                     </div>
                  )}
                  
                  {message.isThinking && !message.content && message.processSteps.length === 0 && (
                    <div className="px-4 py-3">
                      <span className="animate-pulse">▍</span>
                    </div>
                  )}
                </div>
                <div className={`mt-2 text-xs text-slate-500 ${message.isUser ? "text-right" : "text-left"}`}>{formatTime(message.timestamp)}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="px-8 pb-8 pt-4">
          <div className="max-w-2xl mx-auto">
            <div className="backdrop-blur-xl bg-white/30 border border-white/40 rounded-2xl p-4 shadow-xl shadow-gray-500/25">
              <div className="flex items-end space-x-3">
                <Button variant="ghost" size="icon" className="text-slate-600 hover:bg-white/20 rounded-full mb-1 flex-shrink-0"><Paperclip className="h-5 w-5" /></Button>
                <div className="flex-1">
                  <textarea
                    ref={textareaRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="请告诉Hive你需要什么帮助... (Cmd/Ctrl+Enter 发送)"
                    className="w-full bg-transparent border-0 resize-none outline-none focus:ring-0 placeholder:text-slate-500 text-slate-700 leading-relaxed py-2"
                    disabled={isAgentThinking}
                    rows={1}
                  />
                </div>
                <Button variant="ghost" size="icon" className="text-slate-600 hover:bg-white/20 rounded-full mb-1 flex-shrink-0"><Mic className="h-5 w-5" /></Button>
                <Button onClick={handleSendMessage} disabled={!inputValue.trim() || isAgentThinking} className="bg-blue-500/80 hover:bg-blue-600/80 text-white rounded-full p-3 h-auto w-auto flex-shrink-0 backdrop-blur-sm disabled:opacity-50 mb-1"><Send className="h-4 w-4" /></Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}