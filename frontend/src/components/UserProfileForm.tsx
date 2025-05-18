import React, { useState } from 'react';
import styled from 'styled-components';

const Container = styled.div`
  max-width: 500px;
  margin: 30px auto;
  padding: 24px;
  background: #fafafa;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
`;
const Title = styled.h3`
  margin-bottom: 18px;
  text-align: center;
`;
const Input = styled.input`
  width: 100%;
  padding: 8px;
  margin-bottom: 14px;
  border: 1px solid #ccc;
  border-radius: 5px;
`;
const Label = styled.label`
  font-size: 0.95rem;
  margin-bottom: 4px;
  display: block;
`;
const Row = styled.div`
  display: flex;
  gap: 12px;
`;
const Checkbox = styled.input`
  margin-right: 6px;
`;
const Button = styled.button`
  width: 100%;
  padding: 10px;
  background: #388e3c;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
`;

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

const UserProfileForm: React.FC<{ onSave: (profile: UserProfile) => void, initial?: UserProfile }> = ({ onSave, initial }) => {
  const [profile, setProfile] = useState<UserProfile>(initial || {
    name: '',
    email: '',
    uv_sensitivity: 3,
    pollen_sensitivity: 3,
    alert_threshold: 5,
    notification_preferences: { email: true, push: false },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    if (name === 'email' || name === 'name') {
      setProfile(p => ({ ...p, [name]: value }));
    } else if (name === 'uv_sensitivity' || name === 'pollen_sensitivity' || name === 'alert_threshold') {
      setProfile(p => ({ ...p, [name]: Number(value) }));
    } else if (name === 'notify_email' || name === 'notify_push') {
      setProfile(p => ({
        ...p,
        notification_preferences: {
          ...p.notification_preferences,
          [name === 'notify_email' ? 'email' : 'push']: checked
        }
      }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(profile);
  };

  return (
    <Container>
      <Title>User Profile</Title>
      <form onSubmit={handleSubmit}>
        <Label>Name</Label>
        <Input name="name" value={profile.name} onChange={handleChange} required />
        <Label>Email</Label>
        <Input name="email" type="email" value={profile.email} onChange={handleChange} required />
        <Row>
          <div style={{ flex: 1 }}>
            <Label>UV Sensitivity (1-5)</Label>
            <Input name="uv_sensitivity" type="number" min={1} max={5} value={profile.uv_sensitivity} onChange={handleChange} required />
          </div>
          <div style={{ flex: 1 }}>
            <Label>Pollen Sensitivity (1-5)</Label>
            <Input name="pollen_sensitivity" type="number" min={1} max={5} value={profile.pollen_sensitivity} onChange={handleChange} required />
          </div>
        </Row>
        <Label>Alert Threshold (1-10)</Label>
        <Input name="alert_threshold" type="number" min={1} max={10} value={profile.alert_threshold} onChange={handleChange} required />
        <Label>Notification Preferences</Label>
        <Row>
          <label><Checkbox type="checkbox" name="notify_email" checked={profile.notification_preferences.email} onChange={handleChange} />Email</label>
          <label><Checkbox type="checkbox" name="notify_push" checked={profile.notification_preferences.push} onChange={handleChange} />Push</label>
        </Row>
        <Button type="submit">Save Profile</Button>
      </form>
    </Container>
  );
};

export default UserProfileForm; 