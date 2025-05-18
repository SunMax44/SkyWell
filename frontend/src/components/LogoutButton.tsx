import React from 'react';
import styled from 'styled-components';

const Button = styled.button`
  padding: 6px 16px;
  background: transparent;
  color: #1976d2;
  border: 1px solid #1976d2;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  margin-left: 16px;
`;

const LogoutButton: React.FC<{ onLogout: () => void }> = ({ onLogout }) => (
  <Button onClick={onLogout}>Logout</Button>
);

export default LogoutButton; 