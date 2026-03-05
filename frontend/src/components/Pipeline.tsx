"use client";
import { useEffect, useRef, useCallback } from "react";
import type { Task } from "@/app/page";

const API = "http://localhost:8000";

const AGENTS = [
  { key: "planner",    icon: "🧠", label: "Planner",    desc: "Breaking down request" },
  { key: "researcher", icon: "🔍", label: "Researcher",  desc: "Gathering information" },
  { key: "writer",     icon: "✍️",  label: "Writer",     desc: "Synthesizing report" },
  { key: "reviewer",   icon: "✅", label: "Reviewer",   desc: "Evaluating quality" },
];

const STATUS_COLOR: Record<string, string> = {
  pending:     "bg-gray-700",
  planning:    "bg-indigo-600",
  researching: "bg-blue-600",
  writing:     "bg-amber-500",
  revising:    "bg-orange-500",
  reviewing:   "bg-purple-600",
  done:        "bg-emerald-600",
  failed:      "bg-red-600",
};

const PROGRESS: Record<string, number> = {
  pending: 0, planning: 15, researching: 35,
  writing: 60, reviewing: 75, revising: 85, done: 100, failed: 0,
};

function getAgentStatus(agentKey: string, task: Task): "done" | "active" | "pending" {
  const completedAgents = (task.steps ?? [])
    .filter(s => s.status === "done")
    .map(s => s.agent);
  if (completedAgents.includes(agentKey)) return "done";
  if (task.current_agent === agentKey) return "active";
  return "pending";
}

type Props = { task: Task; onTaskUpdate: (t: Task) => void };

export default function Pipeline({ task, onTaskUpdate }: Props) {
  // Use a ref for the callback so the interval always has the latest version
  // without needing to be restarted
  const onTaskUpdateRef = useRef(onTaskUpdate);
  useEffect(() => { onTaskUpdateRef.current = onTaskUpdate; }, [onTaskUpdate]);

  const taskIdRef = useRef(task.id);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isPollingRef = useRef(false);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
      isPollingRef.current = false;
    }
  }, []);

  const startPolling = useCallback((id: string) => {
    if (isPollingRef.current) return; // already polling
    isPollingRef.current = true;

    pollRef.current = setInterval(async () => {
      try {
        // Always fetch fresh status — never rely on stale closure
        const statusRes = await fetch(`${API}/tasks/${id}/status`);
        if (!statusRes.ok) return;
        const statusData = await statusRes.json();

        const progress = PROGRESS[statusData.status] ?? 0;

        if (statusData.status === "done" || statusData.status === "failed") {
          stopPolling();
          // Fetch full task (includes report, sub_tasks, research)
          const fullRes = await fetch(`${API}/tasks/${id}`);
          const full: Task = await fullRes.json();
          onTaskUpdateRef.current({ ...full, progress_percent: progress });
        } else {
          // Fetch full task on every poll so sub_tasks & steps stay up to date
          const fullRes = await fetch(`${API}/tasks/${id}`);
          const full: Task = await fullRes.json();
          onTaskUpdateRef.current({ ...full, progress_percent: progress });
        }
      } catch (e) {
        console.error("Polling error:", e);
      }
    }, 1500);
  }, [stopPolling]);

  // Start polling once on mount — never restart it
  useEffect(() => {
    const id = taskIdRef.current;
    if (!id) return;
    startPolling(id);
    return () => stopPolling();
  }, []); // empty deps — run once only

  // Stop polling when task reaches terminal state
  useEffect(() => {
    if (task.status === "done" || task.status === "failed") {
      stopPolling();
    }
  }, [task.status, stopPolling]);

  const status = task.status ?? "pending";
  const barColor = STATUS_COLOR[status] || "bg-gray-700";
  const progress = task.progress_percent ?? PROGRESS[status] ?? 0;
  const isTerminal = status === "done" || status === "failed";

  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <div className="flex justify-between text-xs text-gray-400 mb-2">
          <span className="capitalize font-medium">{status.replace(/_/g, " ")}</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${barColor} ${!isTerminal ? "animate-pulse" : ""}`}
            style={{ width: `${progress}%` }}
          />
        </div>
        {(task.revision_count ?? 0) > 0 && (
          <p className="text-xs text-orange-400 mt-2">
            🔄 Revision #{task.revision_count} in progress
          </p>
        )}
      </div>

      {/* Agent pipeline */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Agent Pipeline</h3>
        <div className="space-y-3">
          {AGENTS.map((agent, i) => {
            const agentStatus = getAgentStatus(agent.key, task);
            const step = (task.steps ?? []).find(
              s => s.agent === agent.key && s.status === "done"
            );
            return (
              <div key={agent.key}>
                <div className={`flex items-center gap-3 p-3 rounded-lg border transition-all ${
                  agentStatus === "active" ? "bg-indigo-950/50 border-indigo-600" :
                  agentStatus === "done"   ? "bg-gray-800/50 border-gray-700" :
                                            "border-gray-800 opacity-40"
                }`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 ${
                    agentStatus === "done"   ? "bg-emerald-700" :
                    agentStatus === "active" ? "bg-indigo-700 animate-pulse" :
                                              "bg-gray-800"
                  }`}>
                    {agentStatus === "done" ? "✓" : agent.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{agent.label}</span>
                      {agentStatus === "active" && (
                        <span className="text-xs text-indigo-400 animate-pulse">Running...</span>
                      )}
                      {agentStatus === "done" && step?.duration_seconds != null && (
                        <span className="text-xs text-gray-500">{step.duration_seconds.toFixed(1)}s</span>
                      )}
                    </div>
                    {agentStatus === "active" && (
                      <p className="text-xs text-gray-400 mt-0.5">{agent.desc}</p>
                    )}
                    {agentStatus === "done" && step?.output && (
                      <p className="text-xs text-gray-400 mt-0.5 truncate">{step.output}</p>
                    )}
                  </div>
                </div>
                {i < AGENTS.length - 1 && (
                  <div className="flex justify-center">
                    <div className="w-px h-3 bg-gray-700" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Sub-tasks */}
      {(task.sub_tasks ?? []).length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Sub-Tasks</h3>
          <div className="space-y-2">
            {(task.sub_tasks ?? []).map(st => (
              <div key={st.id} className="flex items-start gap-2">
                <span className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${
                  st.status === "done" ? "bg-emerald-500" : "bg-gray-600"
                }`} />
                <div>
                  <p className="text-xs text-gray-300">{st.title}</p>
                  <p className="text-xs text-gray-500">{st.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {status === "failed" && task.error && (
        <div className="bg-red-950/50 border border-red-800 rounded-xl p-4">
          <p className="text-sm text-red-400 font-medium mb-1">Pipeline Failed</p>
          <p className="text-xs text-red-300">{task.error}</p>
        </div>
      )}
    </div>
  );
}