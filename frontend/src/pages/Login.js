import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styles from './Auth.module.css';
import logo from '../assets/logo.png';
import illustration from '../assets/login-illustration.png';

const Login = () => {
  // --- This original code is untouched ---
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ username: '', password: '', rememberMe: false });
  const [error, setError] = useState('');
  // --- End of untouched original code ---

  // --- START OF NEW EDIT: Define the API URL from environment variables ---
  const API_URL = process.env.REACT_APP_API_BASE_URL || '';
  // --- END OF NEW EDIT ---

  // --- This original code is untouched ---
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prevState => ({
      ...prevState,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  // --- End of untouched original code ---

  const handleSubmit = async (e) => {
    // --- This original code is untouched ---
    e.preventDefault();
    setError('');
    // --- End of untouched original code ---

    try {
      // --- START OF NEW EDIT: Replace hardcoded localhost ---
      const response = await fetch(`${API_URL}/api/v1/users/login`, {
      // --- END OF NEW EDIT ---
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      // --- This original code is untouched ---
      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || 'Login failed.');
      } else {
        localStorage.setItem('accessToken', data.access_token);
        navigate('/');
      }
    } catch (err) {
      setError('Could not connect to the server.');
    }
  };

  return (
    <div className={styles.authContainer}>
      <div className={styles.illustrationWrapper}>
        <img src={illustration} alt="Person with a tablet" className={styles.illustration} />
      </div>
      <div className={styles.formWrapper}>
        <div className={styles.formBox}>
          <div className={styles.logoContainer}>
            <img src={logo} alt="EduConnect Logo" />
            <span className={styles.logoText}>EduConnect</span>
          </div>
          <h2 className={styles.title}>Welcome to EduConnect! 👋</h2>
          <p className={styles.subtitle}>Please sign-in to your account and start the adventure</p>

          <form onSubmit={handleSubmit}>
            <div className={styles.inputGroup}>
              <label htmlFor="username">Username</label>
              <input 
                type="text" id="username" name="username"
                placeholder="Enter your username"
                value={formData.username} onChange={handleChange} required 
              />
            </div>
            <div className={styles.inputGroup}>
              <div className={styles.labelWrapper}>
                <label htmlFor="password">Password</label>
                <a href="/forgot-password" className={styles.forgotLink}>Forgot Password?</a>
              </div>
              <input 
                type="password" id="password" name="password"
                placeholder="············"
                value={formData.password} onChange={handleChange} required
              />
            </div>
            <div className={styles.checkboxGroup}>
              <input 
                type="checkbox" id="rememberMe" name="rememberMe"
                checked={formData.rememberMe} onChange={handleChange}
              />
              <label htmlFor="rememberMe">Remember Me</label>
            </div>
            {error && <p className={styles.fieldError}>{error}</p>}
            <button type="submit" className={styles.submitButton}>Sign In</button>
          </form>

          <p className={styles.authLink}>
            New on our platform? <Link to="/signup">Create an account</Link>
          </p>
        </div>
      </div>
    </div>
  );
  // --- End of untouched original code ---
};

export default Login;