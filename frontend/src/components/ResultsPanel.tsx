"use client";
import { useState } from "react";
import type { Task } from "@/app/page";

type Props = { task: Task };

export default function ResultsPanel({ task }: Props) {
  const [activeTab, setActiveTab] = useState<"report" | "research" | "steps">("report");

  const isDone = task.status === "done";
  const hasReport = !!(task.final_report || task.draft_report);
  const reviewDecision = task.review_decision ?? null;
  const revisionCount = task.revision_count ?? 0;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      {/* Task header */}
      <div className="px-5 py-4 border-b border-gray-800">
        <p className="text-xs text-gray-500 mb-1">Task Request</p>
        <p className="text-sm text-gray-200">{task.user_request}</p>
      </div>

      {/* Reviewer feedback banner */}
      {task.review_feedback && (
        <div className={`px-5 py-3 border-b ${
          reviewDecision === "approved"
            ? "bg-emerald-950/50 border-emerald-800"
            : "bg-orange-950/50 border-orange-800"
        }`}>
          <div className="flex items-start gap-2">
            <span>{reviewDecision === "approved" ? "✅" : "🔄"}</span>
            <div>
              <p className={`text-xs font-semibold mb-0.5 ${
                reviewDecision === "approved" ? "text-emerald-400" : "text-orange-400"
              }`}>
                Reviewer: {reviewDecision === "approved" ? "Approved" : "Revision Requested"}
              </p>
              <p className="text-xs text-gray-300">{task.review_feedback}</p>
              {revisionCount > 0 && (
                <p className="text-xs text-gray-500 mt-1">
                  Report revised {revisionCount} time{revisionCount > 1 ? "s" : ""}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-800">
        {[
          { key: "report", label: "📄 Final Report" },
          { key: "research", label: "🔍 Research" },
          { key: "steps", label: "📋 Agent Steps" },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as typeof activeTab)}
            className={`flex-1 text-xs py-3 font-medium transition-colors ${
              activeTab === tab.key
                ? "text-white border-b-2 border-indigo-500"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="p-5 max-h-[65vh] overflow-y-auto">
        {activeTab === "report" && (
          <div>
            {!hasReport ? (
              <div className="text-center py-16 text-gray-500">
                <div className="text-4xl mb-3">⏳</div>
                <p className="text-sm">Agents are working on your report...</p>
                <p className="text-xs mt-1 text-gray-600">
                  {task.status === "planning" && "Planning sub-tasks..."}
                  {task.status === "researching" && "Gathering research..."}
                  {task.status === "writing" && "Writing the report..."}
                  {task.status === "reviewing" && "Reviewing the draft..."}
                  {task.status === "revising" && "Revising based on feedback..."}
                </p>
              </div>
            ) : (
              <div>
                {!isDone && (
                  <div className="mb-4 bg-amber-950/50 border border-amber-800 rounded-lg px-4 py-2">
                    <p className="text-xs text-amber-400">⚠️ Draft in progress — final report pending review</p>
                  </div>
                )}
                <div className="prose prose-invert prose-sm max-w-none">
                  <MarkdownRenderer content={task.final_report || task.draft_report || ""} />
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "research" && (
          <div className="space-y-4">
            {(task.sub_tasks ?? []).length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-8">Research not started yet...</p>
            ) : (
              (task.sub_tasks ?? []).map(st => (
                <div key={st.id} className="border border-gray-800 rounded-lg overflow-hidden">
                  <div className="flex items-center gap-2 px-4 py-2 bg-gray-800/50">
                    <span className={`w-2 h-2 rounded-full ${st.status === "done" ? "bg-emerald-500" : "bg-gray-600"}`} />
                    <span className="text-sm font-medium">{st.title}</span>
                  </div>
                  {st.research_result ? (
                    <div className="px-4 py-3">
                      <pre className="text-xs text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">
                        {st.research_result}
                      </pre>
                    </div>
                  ) : (
                    <div className="px-4 py-3">
                      <p className="text-xs text-gray-600 italic">{st.description}</p>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "steps" && (
          <div className="space-y-3">
            {(task.steps ?? []).length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-8">Pipeline not started yet...</p>
            ) : (
              (task.steps ?? []).map((step, i) => (
                <div key={i} className={`border rounded-lg p-4 ${
                  step.status === "done" ? "border-gray-700 bg-gray-800/30" :
                  step.status === "running" ? "border-indigo-700 bg-indigo-950/30" :
                  "border-red-800 bg-red-950/30"
                }`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-semibold uppercase tracking-wider ${
                        step.status === "done" ? "text-emerald-400" :
                        step.status === "running" ? "text-indigo-400" : "text-red-400"
                      }`}>
                        {step.agent}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        step.status === "done" ? "bg-emerald-900 text-emerald-300" :
                        step.status === "running" ? "bg-indigo-900 text-indigo-300" :
                        "bg-red-900 text-red-300"
                      }`}>
                        {step.status}
                      </span>
                    </div>
                    {step.duration_seconds != null && (
                      <span className="text-xs text-gray-500">{step.duration_seconds.toFixed(1)}s</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mb-1">
                    <span className="text-gray-600">Input: </span>{step.input_summary}
                  </p>
                  {step.output && (
                    <p className="text-xs text-gray-300">
                      <span className="text-gray-600">Output: </span>{step.output}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Simple markdown renderer — converts ## headings, **bold**, --- to HTML
function MarkdownRenderer({ content }: { content: string }) {
  const lines = content.split("\n");

  return (
    <div className="space-y-1">
      {lines.map((line, i) => {
        if (line.startsWith("# ")) return <h1 key={i} className="text-xl font-bold text-white mt-4 mb-2">{line.slice(2)}</h1>;
        if (line.startsWith("## ")) return <h2 key={i} className="text-base font-semibold text-indigo-300 mt-4 mb-1">{line.slice(3)}</h2>;
        if (line.startsWith("### ")) return <h3 key={i} className="text-sm font-semibold text-gray-200 mt-3 mb-1">{line.slice(4)}</h3>;
        if (line.trim() === "---") return <hr key={i} className="border-gray-700 my-4" />;
        if (line.trim() === "") return <div key={i} className="h-2" />;
        if (line.startsWith("- ") || line.startsWith("* ")) {
          const text = line.slice(2).replace(/\*\*(.*?)\*\*/g, "$1");
          return <li key={i} className="text-sm text-gray-300 ml-4 list-disc">{text}</li>;
        }
        if (line.match(/^\d+\./)) {
          const text = line.replace(/^\d+\.\s*/, "").replace(/\*\*(.*?)\*\*/g, "$1");
          return <li key={i} className="text-sm text-gray-300 ml-4 list-decimal">{text}</li>;
        }
        if (line.startsWith(">")) {
          return <blockquote key={i} className="border-l-2 border-indigo-600 pl-3 text-sm text-gray-400 italic">{line.slice(1)}</blockquote>;
        }
        // Inline bold
        const parts = line.split(/\*\*(.*?)\*\*/g);
        return (
          <p key={i} className="text-sm text-gray-300 leading-relaxed">
            {parts.map((p, j) => j % 2 === 1 ? <strong key={j} className="text-white font-semibold">{p}</strong> : p)}
          </p>
        );
      })}
    </div>
  );
}