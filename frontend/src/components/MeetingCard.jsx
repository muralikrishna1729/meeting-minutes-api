import { Link } from "react-router-dom";
import StatusBadge from "./StatusBadge";
import { useState } from "react";

function getPreviewTitle(text) {
  if (!text) return "Untitled meeting";
  const firstLine = text.split("\n")[0].trim();
  return firstLine.length > 60 ? firstLine.slice(0, 60) + "…" : firstLine;
}

export default function MeetingCard({ meeting }) {
  const [open, setOpen] = useState(false);
  const formattedDate = new Date(meeting.created_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <div className="w-full">
      <Link
        to={`/minutes/${meeting.id}`}
        className="block bg-[var(--card-bg)] border rounded-lg p-4 hover:shadow-md transition-shadow w-full"
      >
        <div className="flex items-start justify-between mb-2 gap-3">
          <h3 className="font-semibold text-[var(--text-h)] truncate flex-1">
            {getPreviewTitle(meeting.original_text)}
          </h3>
          <StatusBadge status={meeting.status} />
        </div>

        <p className="text-sm text-[var(--muted)] mb-2">{formattedDate}</p>

        {meeting.summary && (
          <p className="text-sm text-[var(--text)] line-clamp-2">{meeting.summary}</p>
        )}
      </Link>

      <div className="mt-2 flex items-center gap-2">
        <button
          onClick={() => setOpen(true)}
          className="text-sm text-[var(--accent-700)] hover:underline"
        >
          Quick view
        </button>
        <Link to={`/minutes/${meeting.id}`} className="text-sm text-[var(--muted)] hover:text-[var(--accent-700)]">
          Open
        </Link>
      </div>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6">
          <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <div className="relative max-w-2xl w-full bg-[var(--card-bg)] rounded-lg p-6 shadow-lg" style={{border: '1px solid var(--border)'}}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold">{getPreviewTitle(meeting.original_text)}</h3>
                <p className="text-xs text-[var(--muted)]">{formattedDate}</p>
              </div>
              <div className="text-right">
                <StatusBadge status={meeting.status} />
              </div>
            </div>

            {meeting.summary && (
              <div className="mb-4">
                <h4 className="text-sm font-semibold mb-1">Summary</h4>
                <p className="text-sm text-[var(--text)] whitespace-pre-wrap">{meeting.summary}</p>
              </div>
            )}

            <div className="mb-2">
              <h4 className="text-sm font-semibold mb-1">Transcript (excerpt)</h4>
              <pre className="text-sm text-[var(--muted)] max-h-40 overflow-y-auto whitespace-pre-wrap p-3 bg-[var(--bg)] rounded">{meeting.original_text.slice(0, 1200)}</pre>
            </div>

            <div className="mt-4 flex justify-end">
              <button onClick={() => setOpen(false)} className="px-4 py-2 rounded bg-[var(--muted)] text-white">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}