"use client"

import { BrainCircuit, Wrench, FileCheck2, Loader2, CheckCircle2, AlertCircle, ChevronRight, ChevronDown, Bot } from "lucide-react";
import { useState, FC, ReactNode } from "react";

// 导出接口，供ChatApp使用
export interface ProcessStep {
  id: string;
  type: 'PLANNING' | 'TOOL_CALL' | 'TOOL_RESULT';
  title: string;
  content?: any;
  status: 'running' | 'done' | 'error';
}

interface ProcessStepsRendererProps {
  steps: ProcessStep[];
}

// --- 【核心改进】: 一个更智能的内容渲染组件 ---
const StepContent: FC<{ content: any; stepType: ProcessStep['type'] }> = ({ content, stepType }) => {
  if (!content) return null;

  // 1. 如果内容是Tavily的搜索结果，进行特殊的美化渲染
  if (stepType === 'TOOL_CALL' && content.tool_input?.answer) {
    const answer = JSON.parse(content.tool_input.answer);
    if (Array.isArray(answer)) {
      return (
        <div className="mt-1 ml-7 pl-4 border-l border-slate-300/80 space-y-2 py-1">
          {answer.map((item: any, index: number) => (
            <div key={index} className="text-xs bg-slate-100 p-2 rounded">
              <p className="font-semibold text-slate-700">{item.title}</p>
              <p className="text-slate-600 mt-1">{item.content.replace(/\\n/g, ' ')}</p>
              <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline mt-1 block truncate">
                {item.url}
              </a>
            </div>
          ))}
        </div>
      );
    }
  }

  // 2. 对于其他情况，进行通用的JSON美化
  let formattedContent: string;
  try {
    // 检查content是否已经是对象，或者是一个JSON字符串
    const objectToFormat = typeof content === 'string' ? JSON.parse(content) : content;
    // 移除不必要的 `\n` 和多余的转义符，让JSON更干净
    formattedContent = JSON.stringify(objectToFormat, null, 2).replace(/\\n/g, '\n');
  } catch (e) {
    formattedContent = String(content);
  }

  return (
    <div className="mt-1 ml-7 pl-4 border-l border-slate-300/80 py-1">
      <pre className="bg-slate-100 text-slate-600 p-2 rounded-md text-xs whitespace-pre-wrap break-all">
        <code>{formattedContent}</code>
      </pre>
    </div>
  );
};

export const ProcessStepsRenderer: FC<ProcessStepsRendererProps> = ({ steps }) => {
  const [expandedStepId, setExpandedStepId] = useState<string | null>(null);

  const toggleExpand = (stepId: string) => {
    setExpandedStepId(currentId => (currentId === stepId ? null : stepId));
  };

  const ICONS: Record<ProcessStep['type'], ReactNode> = {
    PLANNING: <BrainCircuit className="h-4 w-4 text-purple-600" />,
    TOOL_CALL: <Wrench className="h-4 w-4 text-blue-600" />,
    TOOL_RESULT: <FileCheck2 className="h-4 w-4 text-green-600" />,
  };

  if (!steps || steps.length === 0) return null;

  return (
    // --- 【UI美化】: 增加一个独特的背景板和标题 ---
    <div className="bg-white/50 rounded-lg p-3 space-y-1">
      <div className="flex items-center space-x-2 mb-2">
        <Bot className="h-4 w-4 text-slate-500" />
        <h3 className="text-xs font-semibold text-slate-600 tracking-wider uppercase">Hive 执行过程</h3>
      </div>
      <div className="space-y-1">
        {steps.map((step) => {
          const isExpanded = expandedStepId === step.id;
          const hasContent = step.content && (typeof step.content !== 'object' || Object.keys(step.content).length > 0);
          
          return (
            <div key={step.id}>
              <div 
                className={`flex items-center space-x-3 p-1 rounded-md transition-colors duration-200 ${hasContent ? 'cursor-pointer hover:bg-black/5' : ''}`}
                onClick={hasContent ? () => toggleExpand(step.id) : undefined}
              >
                <div className="w-5 flex-shrink-0 flex items-center justify-center">
                  {step.status === 'running' && <Loader2 className="h-4 w-4 animate-spin text-slate-400" />}
                  {step.status === 'done' && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                  {step.status === 'error' && <AlertCircle className="h-4 w-4 text-red-500" />}
                </div>
                
                <div className="flex-shrink-0">{ICONS[step.type]}</div>

                {/* --- 【工具名美化】--- */}
                <p className="text-sm font-medium text-slate-700 flex-grow" dangerouslySetInnerHTML={{ 
                  __html: step.title.replace(/\[(.*?)\]/g, '<code class="bg-slate-200/80 text-slate-800 font-mono text-xs not-italic px-1 py-0.5 rounded">[$1]</code>')
                }} />
                
                {hasContent && (
                  <div className="flex-shrink-0">
                    {isExpanded ? <ChevronDown className="h-4 w-4 text-slate-500" /> : <ChevronRight className="h-4 w-4 text-slate-400" />}
                  </div>
                )}
              </div>

              {isExpanded && <StepContent content={step.content} stepType={step.type} />}
            </div>
          );
        })}
      </div>
    </div>
  );
};