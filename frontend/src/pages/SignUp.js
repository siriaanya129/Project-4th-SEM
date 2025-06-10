import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import PrivacyModal from '../components/PrivacyModal';
import styles from './Auth.module.css';
import logo from '../assets/logo.png';
import illustration from '../assets/signup-illustration.png';

const SignUp = () => {
  // --- This original code is untouched ---
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    terms: false,
  });

  const [errors, setErrors] = useState({});
  const [isModalOpen, setModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  // --- End of untouched original code ---

  // --- START OF NEW EDIT: Define the API URL from environment variables ---
  // This makes the code flexible for both local development and Vercel deployment.
  // It will use your .env file locally, and your Vercel environment variables in production.
  const API_URL = process.env.REACT_APP_API_BASE_URL || '';
  // --- END OF NEW EDIT ---

  // --- This original code is untouched ---
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prevState => ({
      ...prevState,
      [name]: type === 'checkbox' ? checked : value
    }));
    if (errors[name]) {
      setErrors(prevErrors => ({ ...prevErrors, [name]: '' }));
    }
    if (errors.general) {
        setErrors(prevErrors => ({ ...prevErrors, general: '' }));
    }
  };
  // --- End of untouched original code ---

  const handleSubmit = async (e) => {
    // --- This original code is untouched ---
    e.preventDefault();
    setIsSubmitting(true);

    const newErrors = {};
    if (formData.username.length < 3) newErrors.username = "Username must be at least 3 characters.";
    else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) newErrors.username = "Username can only contain letters, numbers, and _.";
    if (!formData.email.endsWith('@rvce.edu.in')) newErrors.email = "Only @rvce.edu.in email is allowed.";
    if (formData.password.length < 8) newErrors.password = "Password must be at least 8 characters.";
    if (!formData.terms) newErrors.terms = "You must agree to the terms.";

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setIsSubmitting(false);
      return;
    }
    // --- End of untouched original code ---

    try {
      // --- START OF NEW EDIT: Replace hardcoded localhost ---
      const usernameCheckResponse = await fetch(`${API_URL}/api/v1/users/check-username/${formData.username}`);
      // --- END OF NEW EDIT ---
      const usernameData = await usernameCheckResponse.json();

      if (usernameData.username_exists) {
        setErrors({ username: 'This username is already taken.' });
        setIsSubmitting(false);
        return;
      }
    } catch (error) {
      setErrors({ general: 'Could not verify username. Check server connection.' });
      setIsSubmitting(false);
      return;
    }
    
    try {
      // --- START OF NEW EDIT: Replace hardcoded localhost ---
      const registerResponse = await fetch(`${API_URL}/api/v1/users/register`, {
      // --- END OF NEW EDIT ---
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: formData.username,
          email: formData.email,
          password: formData.password,
        }),
      });
      const registerData = await registerResponse.json();

      if (!registerResponse.ok) {
        setErrors({ general: registerData.detail || 'An unknown error occurred.' });
      } else {
        localStorage.setItem('accessToken', registerData.access_token);
        alert('Registration successful! Welcome!');
        navigate('/');
      }
    } catch (error) {
      setErrors({ general: 'Could not connect to the server for registration.' });
    }
    
    // --- This original code is untouched ---
    setIsSubmitting(false);
  };

  return (
    <>
      <div className={styles.authContainer}>
        <div className={styles.illustrationWrapper}>
          <img src={illustration} alt="Person using a laptop" className={styles.illustration} />
        </div>
        <div className={styles.formWrapper}>
          <div className={styles.formBox}>
            <div className={styles.logoContainer}>
              <img src={logo} alt="EduConnect Logo" />
              <span className={styles.logoText}>EduConnect</span>
            </div>
            <h2 className={styles.title}>Adventure starts here 🚀</h2>
            <p className={styles.subtitle}>Make your app management easy and fun!</p>

            <form onSubmit={handleSubmit} noValidate>
              <div className={styles.inputGroup}>
                <label htmlFor="username">Username</label>
                <input
                  type="text" id="username" name="username"
                  placeholder="Enter your username"
                  value={formData.username} onChange={handleChange}
                  className={errors.username ? styles.inputError : ''}
                  autoComplete="username"
                />
                {errors.username && <p className={styles.fieldError}>{errors.username}</p>}
              </div>

              <div className={styles.inputGroup}>
                <label htmlFor="email">Email</label>
                <input
                  type="email" id="email" name="email"
                  placeholder="your.name@rvce.edu.in"
                  value={formData.email} onChange={handleChange}
                  className={errors.email ? styles.inputError : ''}
                  autoComplete="email"
                />
                {errors.email && <p className={styles.fieldError}>{errors.email}</p>}
              </div>

              <div className={styles.inputGroup}>
                <label htmlFor="password">Password</label>
                <input
                  type="password" id="password" name="password"
                  placeholder="Must be 8-32 characters long"
                  value={formData.password} onChange={handleChange}
                  className={errors.password ? styles.inputError : ''}
                  autoComplete="new-password"
                />
                 {errors.password && <p className={styles.fieldError}>{errors.password}</p>}
              </div>

              <div className={styles.checkboxGroup}>
                <input
                  type="checkbox" id="terms" name="terms"
                  checked={formData.terms} onChange={handleChange}
                />
                <label htmlFor="terms">
                  I agree to <span className={styles.privacyLink} onClick={() => setModalOpen(true)}>privacy policy & terms</span>
                </label>
              </div>
              
              {errors.terms && <p className={styles.fieldError}>{errors.terms}</p>}
              {errors.general && <p className={styles.fieldErrorGeneral}>{errors.general}</p>}
              
              <button 
                type="submit" 
                className={styles.submitButton}
                disabled={isSubmitting}
              >
                {isSubmitting ? "Signing Up..." : "Sign Up"}
              </button>
            </form>

            <p className={styles.authLink}>
              Already have an account? <Link to="/login">Sign in instead</Link>
            </p>
          </div>
        </div>
      </div>
      
      <PrivacyModal isOpen={isModalOpen} onClose={() => setModalOpen(false)} />
    </>
  );
};
// --- End of untouched original code ---

export default SignUp;