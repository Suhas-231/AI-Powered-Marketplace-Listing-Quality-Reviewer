import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';

const UserContext = createContext(null);

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get('/api/profile');
      if (res.data?.success && res.data?.user) {
        setUser(res.data.user);
      }
    } catch (err) {
      console.error('Failed to fetch user profile:', err);
      setError(err.response?.data?.message || err.message || 'Failed to load user profile');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const updateProfile = async ({ name, email }) => {
    const res = await api.put('/api/profile', { name, email });
    if (res.data?.success && res.data?.user) {
      setUser(res.data.user);
      return res.data;
    }
    throw new Error(res.data?.message || 'Failed to update profile');
  };

  return (
    <UserContext.Provider value={{ user, loading, error, fetchProfile, updateProfile }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
