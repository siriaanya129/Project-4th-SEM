import React, { useState, useEffect } from 'react';
import Navbar from './Navbar';
import ProfilePanel from './ProfilePanel';

const Layout = ({ children }) => {
  const [isPanelOpen, setPanelOpen] = useState(false);
  const [user, setUser] = useState({});
  // Use a separate state to track login status to avoid waiting for the API call
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('accessToken'));

  // This effect runs when the component mounts or when login status changes
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    setIsLoggedIn(!!token);

    if (token) {
      const fetchUserProfile = async () => {
        try {
          const response = await fetch('http://localhost:8000/api/v1/users/me', {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (response.ok) {
            const data = await response.json();
            setUser(data);
          } else {
            // Handle cases where token is invalid/expired
            localStorage.removeItem('accessToken');
            setIsLoggedIn(false);
          }
        } catch (error) {
          console.error("Failed to fetch user profile", error);
        }
      };
      fetchUserProfile();
    }
  }, [isLoggedIn]); // Re-run if login status changes (e.g., after logout)

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    setIsLoggedIn(false);
    setUser({}); // Clear user data
    // The redirect will happen on the ProfilePanel component
  };

  return (
    <>
      {/* The Navbar now receives the user data and a function to open the panel */}
      <Navbar onProfileClick={() => setPanelOpen(true)} user={user} />
      
      {/* The main content of your application will be rendered here */}
      <main>{children}</main>

      {/* The Profile Panel is always in the DOM, but visibility is controlled by CSS */}
      <ProfilePanel 
        isOpen={isPanelOpen} 
        onClose={() => setPanelOpen(false)} 
        user={user} 
        onLogout={handleLogout}
      />
    </>
  );
};

export default Layout;