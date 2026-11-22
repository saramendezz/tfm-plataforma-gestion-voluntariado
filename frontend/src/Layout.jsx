import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

const ROLE_LABELS = {
  volunteer: "Voluntario",
  organization: "Organización",
  admin: "Administrador",
};

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
        {user?.role === "volunteer" && (
          <nav>
            <NavLink to="/perfil-voluntario">Mi perfil</NavLink>
            <NavLink to="/disponibilidad">Disponibilidad</NavLink>
            <NavLink to="/necesidades-compatibles">Necesidades para mí</NavLink>
          </nav>
        )}
        {user?.role === "organization" && (
          <nav>
            <NavLink to="/perfil-organizacion">Mi organización</NavLink>
            <NavLink to="/necesidades">Necesidades</NavLink>
          </nav>
        )}
        {user && (
          <span>
            {user.username} ({ROLE_LABELS[user.role]}){" "}
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