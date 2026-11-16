import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./Layout";
import ProtectedRoute from "./ProtectedRoute";
import Home from "./pages/Home";
import Login from "./pages/Login";
import OrganizationProfile from "./pages/OrganizationProfile";
import Register from "./pages/Register";
import VolunteerProfile from "./pages/VolunteerProfile";
import NeedForm from "./pages/NeedForm";
import Needs from "./pages/Needs";
import Availability from "./pages/Availability";

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
        <Route
          path="/necesidades"
          element={<ProtectedRoute role="organization"><Needs /></ProtectedRoute>}
        />
        <Route
          path="/necesidades/nueva"
          element={<ProtectedRoute role="organization"><NeedForm /></ProtectedRoute>}
        />
        <Route
          path="/necesidades/:id"
          element={<ProtectedRoute role="organization"><NeedForm /></ProtectedRoute>}
        />
        <Route
          path="/disponibilidad"
          element={<ProtectedRoute role="volunteer"><Availability /></ProtectedRoute>}
        />
      </Route>
    </Routes>
  );
}