"use client";
import { useState } from "react";
import type { Task } from "@/app/page";

const API = "http://localhost:8000";

const EXAMPLE_PROMPTS = [
  "Research the pros and cons of microservices vs. monoliths and produce a summary report.",
  "Research the current state of AI and its impact on software development.",
  "Analyze cloud computing adoption: benefits, challenges, and best practices.",
];

type Props = {
  onTaskCreated: (task: Task) => void;
  setLoading: (b: boolean) => void;
  loading: boolean;
};

export default function TaskForm({ onTaskCreated, setLoading, loading }: Props) {
  const [input, setInput] = useState("");
  const [error, setError] = useState("");

  const submit = async (text: string) => {
    if (!text.trim() || text.length < 10) {
      setError("Please enter at least 10 characters.");
      return;
    }
    setError("");
    setLoading(true);

    try {
      // 1. Create the task
      const res = await fetch(`${API}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request: text }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const created = await res.json();

      // 2. Fetch full task data
      const taskRes = await fetch(`${API}/tasks/${created.id}`);
      const task: Task = await taskRes.json();
      onTaskCreated({ ...task, progress_percent: 0 });

    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(`Failed to create task: ${msg}`);
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="relative">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="e.g. Research the pros and cons of microservices vs. monoliths..."
          rows={4}
          className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:border-indigo-500 transition-colors"
          onKeyDown={e => {
            if (e.key === "Enter" && e.metaKey) submit(input);
          }}
        />
        <div className="absolute bottom-3 right-3 text-xs text-gray-600">
          {input.length}/500
        </div>
      </div>

      {error && (
        <p className="text-red-400 text-sm">{error}</p>
      )}

      <button
        onClick={() => submit(input)}
        disabled={loading || !input.trim()}
        className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-800 disabled:text-gray-500 text-white font-medium py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Starting pipeline...
          </>
        ) : (
          "🚀 Launch Agent Pipeline"
        )}
      </button>

      {/* Example prompts */}
      <div className="mt-2">
        <p className="text-xs text-gray-500 mb-2">Try an example:</p>
        <div className="space-y-2">
          {EXAMPLE_PROMPTS.map(p => (
            <button
              key={p}
              onClick={() => { setInput(p); submit(p); }}
              disabled={loading}
              className="w-full text-left text-xs text-gray-400 hover:text-gray-200 bg-gray-900/50 hover:bg-gray-800 border border-gray-800 rounded-lg px-3 py-2 transition-colors"
            >
              {p}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
