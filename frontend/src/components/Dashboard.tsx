import React, { useState } from 'react';
import AlertDisplay from './AlertDisplay';
import UserProfileForm from './UserProfileForm';
import LogoutButton from './LogoutButton';

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

const Dashboard: React.FC<{
  user: string;
  onLogout: () => void;
  onProfileSave: (profile: UserProfile) => void;
}> = ({ user, onLogout, onProfileSave }) => {
  const [profile, setProfile] = useState<UserProfile | null>(null);

  const handleProfileSave = (p: UserProfile) => {
    setProfile(p);
    onProfileSave(p);
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2>Welcome{profile?.name ? `, ${profile.name}` : user ? `, ${user}` : ''}!</h2>
        <LogoutButton onLogout={onLogout} />
      </div>
      <UserProfileForm onSave={handleProfileSave} initial={profile || undefined} />
      <AlertDisplay />
    </div>
  );
};

export default Dashboard; 