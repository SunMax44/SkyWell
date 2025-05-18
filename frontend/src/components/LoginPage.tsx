import React, { useState } from 'react';
import styled from 'styled-components';

const Container = styled.div`
  max-width: 400px;
  margin: 60px auto;
  padding: 32px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
`;
const Title = styled.h2`
  margin-bottom: 24px;
  text-align: center;
`;
const Input = styled.input`
  width: 100%;
  padding: 10px;
  margin-bottom: 16px;
  border: 1px solid #ccc;
  border-radius: 6px;
`;
const Button = styled.button`
  width: 100%;
  padding: 10px;
  background: #1976d2;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
`;
const Error = styled.div`
  color: #d32f2f;
  margin-bottom: 12px;
  text-align: center;
`;

const LoginPage: React.FC<{ onLogin: (email: string) => void }> = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }
    setError('');
    onLogin(email);
  };

  return (
    <Container>
      <Title>Login</Title>
      <form onSubmit={handleSubmit}>
        {error && <Error>{error}</Error>}
        <Input
          type="email"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
        />
        <Input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
        />
        <Button type="submit">Login</Button>
      </form>
    </Container>
  );
};

export default LoginPage; 