import React, { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
import { ThemeProvider } from "./context/ThemeContext";
import ConnectivityBanner from "./components/ConnectivityBanner";
import Sidebar from "./components/Sidebar";
import AgentDeliveryList from "./components/AgentDeliveryList";
import AgentPerformance from "./components/AgentPerformance";
import DispatcherTable from "./components/DispatcherTable";
import AdminPanel from "./components/AdminPanel";
import LoginPage from "./components/LoginPage";
import SignupPage from "./components/SignupPage";
import ForgotPasswordPage from "./components/ForgotPasswordPage";
import ResetPasswordPage from "./components/ResetPasswordPage";
import TrackingPage from "./components/TrackingPage";

function AppShell() {
  const { user, isLoading } = useAuth();
  const [authView, setAuthView] = useState("login");
  const [activeView, setActiveView] = useState(null);

  // Check the URL for a password-reset token (i.e. the person clicked the
  // link from their reset "email" — see services/email.py). This check
  // happens BEFORE the normal logged-in/logged-out branching below, since
  // someone resetting their password is, by definition, not logged in,
  // and shouldn't need to be — clicking the link should work on its own.
  const urlParams = new URLSearchParams(window.location.search);
  const resetToken = urlParams.get("reset_token");
  const trackId = urlParams.get("track");

  if (trackId) {
    return <TrackingPage deliveryId={trackId} />;
  }

  if (resetToken) {
    return (
      <ResetPasswordPage
        token={resetToken}
        onDone={() => {
          // Clear the token from the URL and return to a normal login
          // screen, rather than leaving the reset link sitting in the
          // address bar (which would let the same page reload straight
          // back into the reset form even after finishing).
          window.history.replaceState({}, "", window.location.pathname);
          window.location.reload();
        }}
      />
    );
  }

  if (isLoading) {
    return null; // avoid a login-page flash while checking localStorage
  }

  if (!user) {
    if (authView === "login") {
      return (
        <LoginPage
          onSwitchToSignup={() => setAuthView("signup")}
          onForgotPassword={() => setAuthView("forgot-password")}
        />
      );
    }
    if (authView === "forgot-password") {
      return <ForgotPasswordPage onBackToLogin={() => setAuthView("login")} />;
    }
    return <SignupPage onSwitchToLogin={() => setAuthView("login")} />;
  }

  // Default landing view depends on role, set once we know who's logged in.
  // Admins default to "dashboard" (not "admin") since that's where the
  // actual operational work happens — user management is secondary.
  const currentView =
    activeView ||
    (user.role === "agent" ? "deliveries" : "dashboard");

  return (
    <div className="app-shell">
      <Sidebar activeView={currentView} onNavigate={setActiveView} />

      <div className="main-content">
        <ConnectivityBanner />
        <div style={{ marginTop: "20px" }}>
          {user.role === "agent" && currentView === "deliveries" && <AgentDeliveryList />}
          {user.role === "agent" && currentView === "performance" && <AgentPerformance />}
          {(user.role === "dispatcher" || user.role === "admin") && currentView === "dashboard" && (
            <DispatcherTable />
          )}
          {user.role === "admin" && currentView === "admin" && <AdminPanel />}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <AppShell />
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
