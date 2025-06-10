// In frontend/src/hooks/useAuth.js
import { useState, useEffect } from 'react';

const useAuth = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    setIsLoggedIn(!!token); // !! converts the string/null to a true/false boolean
  }, []); // The empty array means this runs only once when the component mounts

  return { isLoggedIn };
};

export default useAuth;