import { Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <>
      <header className="topbar">
        <strong>Plataforma de voluntariado</strong>
        {user && (
          <span>
            {user.username} ({user.role}){" "}
            <button onClick={handleLogout}>Salir</button>
          </span>
        )}
      </header>
      <main>
        <Outlet />
      </main>
    </>
  );
}