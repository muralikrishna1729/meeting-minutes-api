import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import api from "../api/axios";
import StatusBadge from "../components/StatusBadge";
import Loader from "../components/Loader";

const POLL_INTERVAL = 4000;

export default function MinuteDetail() {
  const { id } = useParams();
  const [meeting, setMeeting] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let intervalId;

    const fetchMeeting = async () => {
      try {
        const res = await api.get(`/minutes/${id}`);
        setMeeting(res.data);
        setError("");

        if (res.data.status === "completed" || res.data.status === "failed") {
          clearInterval(intervalId);
        }
      } catch (err) {
        setError("Failed to load this meeting.");
        clearInterval(intervalId);
      } finally {
        setLoading(false);
      }
    };

    fetchMeeting();
    intervalId = setInterval(fetchMeeting, POLL_INTERVAL);

    return () => clearInterval(intervalId);
  }, [id]);

  if (loading) {
    return <Loader size="lg" />;
  }

  if (error) {
    return <p className="text-red-600 text-center py-12">{error}</p>;
  }

  if (!meeting) {
    return null;
  }

  const isProcessing = meeting.status === "pending" || meeting.status === "processing";

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Meeting Details</h1>
        <StatusBadge status={meeting.status} />
      </div>

      {isProcessing && (
        <div className="bg-[var(--accent-bg)] border rounded-lg p-4 mb-6 flex items-center gap-3" style={{borderColor: 'var(--accent-border)'}}>
          <Loader size="sm" />
          <p className="text-sm text-[var(--accent-700)]">
            Summarization in progress — this page will update automatically.
          </p>
        </div>
      )}

      {meeting.status === "failed" && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-red-800">
            Summarization failed for this meeting. You may need to re-upload the transcript.
          </p>
        </div>
      )}

      {meeting.summary && (
        <section className="mb-6 bg-[var(--card-bg)] border rounded-lg p-6" style={{borderColor: 'var(--border)'}}>
          <h2 className="text-lg font-semibold mb-3">Summary</h2>
          <p className="text-gray-700 whitespace-pre-wrap text-base leading-7">{meeting.summary}</p>
        </section>
      )}

      {meeting.action_items && meeting.action_items.length > 0 && (
        <section className="mb-6 bg-[var(--card-bg)] border rounded-lg p-6" style={{borderColor: 'var(--border)'}}>
          <h2 className="text-lg font-semibold mb-3">Action Items</h2>
          <ul className="space-y-2">
            {meeting.action_items.map((item, i) => (
              <li key={i} className="text-gray-700 pl-3">
                <span className="inline-block w-2 h-2 mr-2 bg-[var(--accent)] rounded-full align-middle" />{item}
              </li>
            ))}
          </ul>
        </section>
      )}

      {meeting.decisions && meeting.decisions.length > 0 && (
        <section className="mb-6 bg-[var(--card-bg)] border rounded-lg p-6" style={{borderColor: 'var(--border)'}}>
          <h2 className="text-lg font-semibold mb-3">Decisions</h2>
          <ul className="space-y-2">
            {meeting.decisions.map((item, i) => (
              <li key={i} className="text-gray-700">{item}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="bg-[var(--card-bg)] border rounded-lg p-4" style={{borderColor: 'var(--border)'}}>
        <h2 className="text-lg font-semibold mb-2">Original Transcript</h2>
        <pre className="text-sm text-[var(--muted)] whitespace-pre-wrap max-h-64 overflow-y-auto p-3 bg-[var(--bg)] rounded">
{meeting.original_text}
        </pre>
      </section>
    </div>
  );
}