import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './components/LoginPage';
import Dashboard from './components/Dashboard';

interface UserProfile {
  name: string;
  email: string;
  uv_sensitivity: number;
  pollen_sensitivity: number;
  alert_threshold: number;
  notification_preferences: {
    email: boolean;
    push: boolean;
  };
}

const App: React.FC = () => {
  const [user, setUser] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);

  const handleLogin = (email: string) => {
    setUser(email);
  };
  const handleLogout = () => {
    setUser(null);
    setProfile(null);
  };
  const handleProfileSave = (p: UserProfile) => {
    setProfile(p);
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={user ? (
            <Dashboard user={user} onLogout={handleLogout} onProfileSave={handleProfileSave} />
          ) : (
            <LoginPage onLogin={handleLogin} />
          )}
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App; 