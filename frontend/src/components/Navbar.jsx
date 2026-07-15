import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="bg-white shadow px-6 py-3 flex items-center justify-between">
      <Link to="/dashboard" className="text-lg font-bold text-blue-600">
        Meeting Minutes
      </Link>

      <div className="flex items-center gap-4">
        {isAdmin && (
          <Link to="/admin" className="text-sm text-gray-600 hover:text-blue-600">
            Admin
          </Link>
        )}

        <span className="text-sm text-gray-500">{user?.email}</span>

        <button
          onClick={handleLogout}
          className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1.5 rounded"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}