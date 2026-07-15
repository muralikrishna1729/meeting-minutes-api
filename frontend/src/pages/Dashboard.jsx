import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../api/axios";
import MeetingCard from "../components/MeetingCard";
import Loader from "../components/Loader";

export default function Dashboard() {
  const [meetings, setMeetings] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchMeetings(searchTerm);
    }, 400);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  const fetchMeetings = async (search) => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/minutes", {
        params: search ? { search } : {},
      });
      setMeetings(res.data);
    } catch (err) {
      setError("Failed to load meetings. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Your Meetings</h1>
        <Link
          to="/upload"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          + Upload Transcript
        </Link>
      </div>

      <input
        type="text"
        placeholder="Search meetings..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="w-full border rounded px-3 py-2 mb-6"
      />

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
        <div className="space-y-3">
          {meetings.map((meeting) => (
            <MeetingCard key={meeting.id} meeting={meeting} />
          ))}
        </div>
      )}
    </div>
  );
}