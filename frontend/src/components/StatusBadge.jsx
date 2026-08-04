const STATUS_STYLES = {
  pending: "bg-gray-100 text-gray-700",
  processing: "bg-yellow-100 text-yellow-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
};

export default function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || "bg-gray-100 text-gray-700";
  const label = status ? String(status).replace(/_/g, " ") : "unknown";

  return (
    <span
      className={`text-xs font-semibold px-2.5 py-1 rounded-full ${style} uppercase tracking-wider`}
    >
      {label}
    </span>
  );
}