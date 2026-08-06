import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../api/axios";
import MeetingCard from "../components/MeetingCard";
import Loader from "../components/Loader";

const PAGE_SIZE = 10;

export default function Dashboard() {
  const [meetings, setMeetings] = useState([]);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchMeetings(page);
  }, [page, query]);

  const fetchMeetings = async (pageNum) => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/minutes/", {
        params: { page: pageNum, page_size: PAGE_SIZE, q: query || undefined },
      });
      setMeetings(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      setError("Failed to load meetings. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
    <input
  type="text"
  value={query}
  onChange={(e) => {
    setQuery(e.target.value);
    setPage(1);           // reset to first page on new search
  }}
  placeholder="Search meetings..."
  className="w-full max-w-xs px-3 py-2 border rounded mb-4"
/>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Your Meetings</h1>
        <Link
          to="/upload"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          + Upload Transcript
        </Link>
      </div>

      {loading && <Loader />}

      {!loading && error && (
        <p className="text-red-600 text-center py-8">{error}</p>
      )}

      {!loading && !error && meetings.length === 0 && (
        <p className="text-gray-500 text-center py-8">
          No meetings found. Upload a transcript to get started.
        </p>
      )}

      {!loading && !error && meetings.length > 0 && (
        <>
          <div className="grid gap-6 mb-6 grid-cols-1 sm:grid-cols-2">
            {meetings.map((meeting) => (
              <MeetingCard key={meeting.id} meeting={meeting} />
            ))}
          </div>

          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => setPage((p) => p - 1)}
              disabled={page <= 1}
              className="px-3 py-1.5 border rounded disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= totalPages}
              className="px-3 py-1.5 border rounded disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}