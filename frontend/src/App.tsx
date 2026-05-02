import { useState } from "react";
import axios from "axios";

const API = axios.create({ baseURL: "/api" });

interface Project {
  id: string;
  title: string;
  author: string;
  premise: string;
}

interface Chapter {
  number: number;
  title: string;
  content: string;
  status: string;
}

export default function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [title, setTitle] = useState("");
  const [premise, setPremise] = useState("");

  const createProject = async () => {
    if (!title.trim()) return;
    setLoading(true);
    try {
      const { data } = await API.post("/projects", { title, premise });
      setProjects([...projects, data]);
      setTitle("");
      setPremise("");
      setSelectedProject(data.id);
      setChapters([]);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const loadChapters = async (projectId: string) => {
    setSelectedProject(projectId);
    setLoading(true);
    try {
      const { data } = await API.get(`/projects/${projectId}/chapters`);
      setChapters(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const generateChapter = async (chapterNumber: number) => {
    if (!selectedProject) return;
    setGenerating(true);
    try {
      const { data } = await API.post("/generate/chapter", {
        project_id: selectedProject,
        chapter_number: chapterNumber,
        outline: `Chapter ${chapterNumber}`,
      });
      if (data.success) {
        await loadChapters(selectedProject);
      }
    } catch (e) {
      console.error(e);
    }
    setGenerating(false);
  };

  const loadProjects = async () => {
    setLoading(true);
    try {
      const { data } = await API.get("/projects");
      setProjects(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-amber-50">
      <header className="bg-white border-b border-amber-200 px-6 py-4">
        <h1 className="text-2xl font-serif text-amber-900">My Novel Assist</h1>
        <p className="text-sm text-amber-600">AI-powered novel writing assistant</p>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left panel — project list & creation */}
        <aside className="space-y-4">
          <div className="bg-white rounded-lg shadow p-4 space-y-3">
            <h2 className="font-serif text-lg text-amber-800">New Project</h2>
            <input
              className="w-full border border-amber-200 rounded px-3 py-2 text-sm"
              placeholder="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <textarea
              className="w-full border border-amber-200 rounded px-3 py-2 text-sm"
              placeholder="Premise (optional)"
              rows={3}
              value={premise}
              onChange={(e) => setPremise(e.target.value)}
            />
            <button
              className="w-full bg-amber-700 text-white rounded py-2 hover:bg-amber-800 disabled:opacity-50"
              disabled={loading || !title.trim()}
              onClick={createProject}
            >
              {loading ? "Creating..." : "Create"}
            </button>
          </div>

          <div className="bg-white rounded-lg shadow p-4 space-y-2">
            <h2 className="font-serif text-lg text-amber-800">Projects</h2>
            <button
              className="w-full text-sm text-amber-600 hover:text-amber-800"
              onClick={loadProjects}
            >
              Refresh
            </button>
            {projects.length === 0 && (
              <p className="text-sm text-gray-400">No projects yet</p>
            )}
            {projects.map((p) => (
              <button
                key={p.id}
                className={`w-full text-left px-3 py-2 rounded text-sm ${
                  selectedProject === p.id
                    ? "bg-amber-100 text-amber-900"
                    : "hover:bg-gray-50"
                }`}
                onClick={() => loadChapters(p.id)}
              >
                {p.title}
              </button>
            ))}
          </div>
        </aside>

        {/* Right panel — chapter list & generation */}
        <section className="md:col-span-2 space-y-4">
          {selectedProject && (
            <>
              <div className="bg-white rounded-lg shadow p-4 space-y-3">
                <h2 className="font-serif text-lg text-amber-800">Generate Chapter</h2>
                <div className="flex gap-2">
                  <button
                    className="bg-amber-700 text-white px-4 py-2 rounded hover:bg-amber-800 disabled:opacity-50 text-sm"
                    disabled={generating}
                    onClick={() => generateChapter(chapters.length + 1)}
                  >
                    {generating ? "Generating..." : "Next Chapter"}
                  </button>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-4 space-y-2">
                <h2 className="font-serif text-lg text-amber-800">Chapters</h2>
                {chapters.length === 0 && (
                  <p className="text-sm text-gray-400">No chapters yet</p>
                )}
                {chapters.map((ch) => (
                  <div
                    key={ch.number}
                    className="border border-amber-100 rounded p-3"
                  >
                    <div className="flex justify-between items-center">
                      <h3 className="font-serif text-amber-900">
                        Ch.{ch.number} {ch.title}
                      </h3>
                      <span className="text-xs text-amber-500">{ch.status}</span>
                    </div>
                    {ch.content && (
                      <p className="text-sm text-gray-600 mt-2 line-clamp-3 whitespace-pre-wrap">
                        {ch.content}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}

          {!selectedProject && (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-400 font-serif">
                Create or select a project to begin
              </p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
