import { Navigate, BrowserRouter, Routes, Route } from "react-router-dom";
import { getSession } from "./auth";

import LandingPage from "./pages/LandingPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import JoinPage from "./pages/JoinPage.jsx";

import AdminLoginPage from "./pages/AdminLoginPage.jsx";
import AdminDashboardPage from "./pages/AdminDashboardPage.jsx";
import CreateHackathonPage from "./pages/CreateHackathonPage.jsx";
import AdminRegistrationsPage from "./pages/AdminRegistrationsPage.jsx";
import AdminAnalyticsPage from "./pages/AdminAnalyticsPage.jsx";
import AdminReviewersPage from "./pages/AdminReviewersPage.jsx";
import AdminBiasPage from "./pages/AdminBiasPage.jsx";
import AdminInsightsPage from "./pages/AdminInsightsPage.jsx";

import ReviewerLoginPage from "./pages/ReviewerLoginPage.jsx";
import ReviewerDashboardPage from "./pages/ReviewerDashboardPage.jsx";
import ReviewerScorePage from "./pages/ReviewerScorePage.jsx";

import MentorLoginPage from "./pages/MentorLoginPage.jsx";
import MentorDashboardPage from "./pages/MentorDashboardPage.jsx";

function RequireRole({ role, redirectTo, children }) {
  const session = getSession();
  if (!session || session.role !== role) {
    return <Navigate to={redirectTo} replace />;
  }
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/join/:token" element={<JoinPage />} />

        <Route path="/participant/login" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={
            <RequireRole role="participant" redirectTo="/participant/login">
              <DashboardPage />
            </RequireRole>
          }
        />

        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route
          path="/admin/dashboard"
          element={
            <RequireRole role="organizer" redirectTo="/admin/login">
              <AdminDashboardPage />
            </RequireRole>
          }
        />
        <Route
          path="/admin/create-hackathon"
          element={
            <RequireRole role="organizer" redirectTo="/admin/login">
              <CreateHackathonPage />
            </RequireRole>
          }
        />
        <Route
          path="/admin/registrations"
          element={
            <RequireRole role="organizer" redirectTo="/admin/login">
              <AdminRegistrationsPage />
            </RequireRole>
          }
        />
        <Route
          path="/admin/analytics"
          element={
            <RequireRole role="organizer" redirectTo="/admin/login">
              <AdminAnalyticsPage />
            </RequireRole>
          }
        />
        <Route
          path="/admin/reviewers"
          element={
            <RequireRole role="organizer" redirectTo="/admin/login">
              <AdminReviewersPage />
            </RequireRole>
          }
        />
        <Route
          path="/admin/bias"
          element={
            <RequireRole role="organizer" redirectTo="/admin/login">
              <AdminBiasPage />
            </RequireRole>
          }
        />
        <Route
          path="/admin/insights"
          element={
            <RequireRole role="organizer" redirectTo="/admin/login">
              <AdminInsightsPage />
            </RequireRole>
          }
        />

        <Route path="/reviewer/login" element={<ReviewerLoginPage />} />
        <Route
          path="/reviewer/dashboard"
          element={
            <RequireRole role="judge" redirectTo="/reviewer/login">
              <ReviewerDashboardPage />
            </RequireRole>
          }
        />
        <Route
          path="/reviewer/score/:teamId"
          element={
            <RequireRole role="judge" redirectTo="/reviewer/login">
              <ReviewerScorePage />
            </RequireRole>
          }
        />

        <Route path="/mentor/login" element={<MentorLoginPage />} />
        <Route
          path="/mentor/dashboard"
          element={
            <RequireRole role="mentor" redirectTo="/mentor/login">
              <MentorDashboardPage />
            </RequireRole>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
