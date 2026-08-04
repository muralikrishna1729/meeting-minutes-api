import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";

const MIN_LENGTH = 10;
const MAX_LENGTH = 50000;

export default function Upload() {
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (text.trim().length < MIN_LENGTH) {
      setError(`Transcript must be at least ${MIN_LENGTH} characters.`);
      return;
    }

    setError("");
    setSubmitting(true);

    try {
      const res = await api.post("/minutes/upload-text", {
        original_text: text,
      });
      navigate(`/minutes/${res.data.meeting_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleFile = (file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setText(String(ev.target.result || ""));
    reader.readAsText(file);
  };

  const onFileChange = (e) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  };

  const onDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Upload Transcript</h1>
      </div>

      <form onSubmit={handleSubmit} className="bg-[var(--card-bg)] border rounded-lg p-6 space-y-4" style={{borderColor: 'var(--border)'}} onDrop={onDrop} onDragOver={(e)=>e.preventDefault()}>
        <div>
          <label className="block text-sm font-medium mb-2">Paste or upload meeting transcript</label>

          <div className="mb-3 flex gap-3">
            <button type="button" onClick={() => fileInputRef.current?.click()} className="px-3 py-2 border rounded-lg text-[var(--muted)]" style={{borderColor: 'var(--border)'}}>Choose file</button>
            <span className="text-xs text-[var(--muted)]">or drag & drop a text file onto this card</span>
          </div>

          <input ref={fileInputRef} type="file" accept="text/*" onChange={onFileChange} className="hidden" />

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            minLength={MIN_LENGTH}
            maxLength={MAX_LENGTH}
            rows={10}
            required
            className="w-full border rounded-lg px-3 py-3 font-mono text-sm bg-[var(--bg)]"
            style={{borderColor: 'var(--border)'}}
            placeholder="Paste the raw meeting transcript here..."
          />
          <p className="text-xs text-[var(--muted)] mt-2 text-right">{text.length} / {MAX_LENGTH}</p>
        </div>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={submitting}
            className="flex-1 bg-[var(--accent)] hover:bg-[var(--accent-700)] text-white py-2 rounded-lg disabled:opacity-50"
          >
            {submitting ? "Uploading..." : "Upload"}
          </button>
          <button
            type="button"
            onClick={() => setText("")}
            className="px-4 py-2 border rounded-lg text-[var(--muted)]"
            style={{borderColor: 'var(--border)'}}
          >
            Clear
          </button>
        </div>
      </form>
    </div>
  );
}