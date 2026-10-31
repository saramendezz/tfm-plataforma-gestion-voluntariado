import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./Layout";
import ProtectedRoute from "./ProtectedRoute";
import Home from "./pages/Home";
import Login from "./pages/Login";
import OrganizationProfile from "./pages/OrganizationProfile";
import Register from "./pages/Register";
import VolunteerProfile from "./pages/VolunteerProfile";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/registro" element={<Register />} />
        <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route
          path="/perfil-voluntario"
          element={<ProtectedRoute role="volunteer"><VolunteerProfile /></ProtectedRoute>}
        />
        <Route
          path="/perfil-organizacion"
          element={<ProtectedRoute role="organization"><OrganizationProfile /></ProtectedRoute>}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}