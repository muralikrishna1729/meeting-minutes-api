import { useState, useEffect } from "react";
import api from "../api/axios";
import Loader from "../components/Loader";

export default function Admin() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedModel, setSelectedModel] = useState("mock");
  const [switching, setSwitching] = useState(false);
  const [switchError, setSwitchError] = useState("");
  const [switchSuccess, setSwitchSuccess] = useState("");

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/admin/stats");
      setStats(res.data);
      setSelectedModel(res.data.current_summarizer);
    } catch (err) {
      setError("Failed to load admin stats.");
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchModel = async (e) => {
    e.preventDefault();
    setSwitching(true);
    setSwitchError("");
    setSwitchSuccess("");

    try {
      await api.post("/admin/model/switch", {
        summarizer_type: selectedModel,
      });
      setSwitchSuccess(`Summarizer switched to ${selectedModel}.`);
      await fetchStats();
    } catch (err) {
      setSwitchError(err.response?.data?.detail || "Failed to switch model.");
    } finally {
      setSwitching(false);
    }
  };

  if (loading) {
    return <Loader size="lg" />;
  }

  if (error) {
    return <p className="text-red-600 text-center py-12">{error}</p>;
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 mb-8">
        <StatCard label="Total Meetings" value={stats.total} />
        <StatCard label="Completed" value={stats.completed} color="text-green-600" />
        <StatCard label="Pending / Processing" value={stats.pending} color="text-yellow-600" />
        <StatCard label="Failed" value={stats.failed} color="text-red-600" />
      </div>

      <div className="bg-white border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-1">Summarizer Model</h2>
        <p className="text-sm text-gray-500 mb-4">
          Current: <span className="font-medium">{stats.current_summarizer}</span>
        </p>

        <form onSubmit={handleSwitchModel} className="flex items-center gap-3">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="mock">mock</option>
            <option value="huggingface">huggingface</option>
          </select>

          <button
            type="submit"
            disabled={switching}
            className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
          >
            {switching ? "Switching..." : "Switch"}
          </button>
        </form>

        {switchError && <p className="text-red-600 text-sm mt-3">{switchError}</p>}
        {switchSuccess && <p className="text-green-600 text-sm mt-3">{switchSuccess}</p>}
      </div>
    </div>
  );
}

function StatCard({ label, value, color = "text-gray-900" }) {
  return (
    <div className="bg-white border rounded-lg p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}