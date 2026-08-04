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
    <nav className="w-full" style={{background: 'var(--nav-bg)', borderBottom: '1px solid rgba(255,255,255,0.04)'}}>
      <div className="w-full max-w-[1400px] mx-auto px-6 py-3 flex items-center gap-4">
        <div className="flex items-center gap-6 min-w-[200px]">
          <Link to="/dashboard" className="text-lg font-semibold" style={{color: 'var(--nav-text)'}}>
            Meeting Minutes
          </Link>
        </div>

        <div className="flex-1 flex items-center justify-center gap-6 text-sm flex-wrap">
          <Link to="/dashboard" className="px-3 py-1 rounded text-[var(--nav-text)]/90 hover:text-[var(--accent-700)]">Dashboard</Link>
          <Link to="/upload" className="px-3 py-1 rounded text-[var(--nav-text)]/90 hover:text-[var(--accent-700)]">Upload</Link>
          {isAdmin && <Link to="/admin" className="px-3 py-1 rounded text-[var(--nav-text)]/90 hover:text-[var(--accent-700)]">Admin</Link>}
          <a href="#" className="px-3 py-1 rounded text-[var(--nav-text)]/90 hover:text-[var(--accent-700)]">Help</a>
          <a href="#" className="px-3 py-1 rounded text-[var(--nav-text)]/90 hover:text-[var(--accent-700)]">Settings</a>
        </div>

        <div className="flex items-center gap-4 min-w-[220px] justify-end">
          <span className="text-sm text-[var(--nav-text)] truncate max-w-xs hidden sm:block">{user?.email}</span>

          <Link to="/upload" className="hidden sm:inline-flex items-center gap-2 bg-[var(--accent)] text-white px-3 py-1.5 rounded-md hover:bg-[var(--accent-700)]">
            New Upload
          </Link>

          <button
            onClick={handleLogout}
            className="text-sm bg-transparent text-[var(--nav-text)] border border-transparent hover:text-white px-3 py-1.5 rounded"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}