"use client";
import { useState } from "react";
import TaskForm from "@/components/TaskForm";
import Pipeline from "@/components/Pipeline";
import ResultsPanel from "@/components/ResultsPanel";

export type AgentStep = {
  agent: string;
  status: string;
  input_summary: string;
  output: string | null;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number | null;
};

export type SubTask = {
  id: string;
  title: string;
  description: string;
  research_result: string | null;
  status: string;
};

export type Task = {
  id: string;
  status: string;
  user_request: string;
  current_agent: string | null;
  progress_percent: number;
  sub_tasks: SubTask[];
  draft_report: string | null;
  final_report: string | null;
  review_decision: string | null;
  review_feedback: string | null;
  revision_count: number;
  steps: AgentStep[];
  error: string | null;
  created_at: string;
};

export default function Home() {
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(false);

  // Accepts a plain Task object — Pipeline always passes a full merged object
  const handleTaskUpdate = (updated: Task) => {
    setTask(updated);
  };

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-sm font-bold">
            M
          </div>
          <div>
            <h1 className="text-lg font-semibold">Multi-Agent Orchestrator</h1>
            <p className="text-xs text-gray-400">AI agents collaborating to research & write reports</p>
          </div>
          {task && (
            <button
              onClick={() => { setTask(null); setLoading(false); }}
              className="ml-auto text-sm text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 px-3 py-1.5 rounded-lg transition-colors"
            >
              ← New Task
            </button>
          )}
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {!task ? (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-10">
              <h2 className="text-3xl font-bold mb-3">What should the agents research?</h2>
              <p className="text-gray-400">
                Submit a research topic and watch four AI agents collaborate in real-time
                to plan, research, write, and review a comprehensive report.
              </p>
            </div>
            <TaskForm onTaskCreated={setTask} setLoading={setLoading} loading={loading} />
            <div className="mt-12 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { icon: "🧠", name: "Planner",    desc: "Breaks your request into sub-tasks" },
                { icon: "🔍", name: "Researcher", desc: "Gathers info for each sub-task" },
                { icon: "✍️",  name: "Writer",    desc: "Synthesizes research into a draft" },
                { icon: "✅", name: "Reviewer",  desc: "Evaluates & approves the report" },
              ].map(a => (
                <div key={a.name} className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
                  <div className="text-2xl mb-2">{a.icon}</div>
                  <div className="font-medium text-sm">{a.name}</div>
                  <div className="text-xs text-gray-500 mt-1">{a.desc}</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Pipeline task={task} onTaskUpdate={handleTaskUpdate} />
            </div>
            <div className="lg:col-span-3">
              <ResultsPanel task={task} />
            </div>
          </div>
        )}
      </div>
    </main>
  );
}