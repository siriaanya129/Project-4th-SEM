// In frontend/src/components/PrivacyModal.js
import React from 'react';
import styles from './PrivacyModal.module.css';

// This is a self-contained component. It doesn't need to know anything
// about the page that opens it, only whether it should be open (`isOpen`)
// and how to close itself (`onClose`).
const PrivacyModal = ({ isOpen, onClose }) => {
  // If the modal is not supposed to be open, we render nothing.
  if (!isOpen) {
    return null;
  }

  return (
    // The backdrop is the semi-transparent black background.
    // Clicking it will close the modal.
    <div className={styles.modalBackdrop} onClick={onClose}>
      {/* We stop click propagation on the content itself, so clicking
          inside the modal doesn't close it. */}
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2>Terms of Service and Privacy Policy</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <div className={styles.modalBody}>
          <p><strong>Last Updated: June 7, 2025</strong></p>
          <p>
            Welcome to EduConnect ("we," "our," "us"). These Terms of Service ("Terms") govern your use of our online learning platform and related services (collectively, the "Service"). By creating an account or using our Service, you agree to be bound by these Terms.
          </p>
          
          <h4>1. Agreement to Terms</h4>
          <p>By accessing or using our Service, you confirm that you can form a binding contract with EduConnect, that you accept these Terms, and that you agree to comply with them. Your access to and use of our Service is also conditioned on your acceptance of and compliance with our Privacy Policy. If you disagree with any part of the terms, then you may not access the Service.</p>
          
          <h4>2. Platform Services</h4>
          <p>EduConnect provides a personalized learning environment designed to assist students in their academic journey. Our core offerings include dynamically generated quizzes, performance analysis, and the generation of customized learning pathways. These tools are designed to be user-friendly and to supplement your studies by identifying areas of strength and weakness, thereby providing a potential opportunity for growth.</p>
          
          <h4>3. User Accounts and Responsibilities</h4>
          <p>To access most features of the Service, you must register for an account. When you create an account, you must provide us with information that is accurate, complete, and current at all times. You are responsible for safeguarding the password that you use to access the Service and for any activities or actions under your password. You agree not to disclose your password to any third party. You must notify us immediately upon becoming aware of any breach of security or unauthorized use of your account. EduConnect cannot and will not be liable for any loss or damage arising from your failure to comply with these security obligations.</p>
          
          <h4>4. Privacy Policy and Information Sharing</h4>
          <p>Our Privacy Policy, which is part of these Terms, describes how we collect, use, and share your personal data. We collect information you provide directly to us, such as your name and email address, and data generated through your use of the Service, such as quiz scores and performance metrics. This data is used exclusively to power the personalization features of the Service, conduct internal analysis for service improvement, and generate your learning pathways. We will not sell, rent, or share your personally identifiable information with third parties for their marketing purposes without your explicit consent.</p>

          <h4>5. Academic Integrity and Platform Use</h4>
          <p>The quizzes and learning materials on EduConnect are designed to be a tool for your personal academic development. The integrity of your learning process is paramount. Therefore, using external aids, including but not limited to AI language models (e.g., ChatGPT), online search engines, or other persons to answer quiz questions, is strictly prohibited and violates the spirit and intended use of the Service. Engaging in such activities constitutes a misuse of the platform and is a disservice to your own educational journey. True growth comes from honest effort and accurately identifying areas that require improvement.</p>
          
          <h4>6. User Conduct</h4>
          <p>You agree not to use the Service to: (a) upload or distribute any computer viruses, worms, or any software intended to damage or alter a computer system or data; (b) interfere with, disrupt, or create an undue burden on servers or networks connected to the Service; (c) attempt to gain unauthorized access to the Service or to other users' accounts. We reserve the right to terminate accounts that are used for such activities.</p>
          
          <h4>7. Intellectual Property</h4>
          <p>The Service and its original content (excluding content provided by users), features, and functionality are and will remain the exclusive property of EduConnect and its licensors. Our trademarks and trade dress may not be used in connection with any product or service without our prior written consent.</p>

          <h4>8. Data Retention and Loss</h4>
          <p>We will make commercially reasonable efforts to store and secure your performance data. However, you acknowledge that no system is infallible. Therefore, EduConnect is not responsible for any data loss, corruption, or unavailability of data that may occur. We recommend that you maintain your own records of significant academic progress if you deem it necessary. The Service is provided as a supplementary tool and should not be considered a system of record.</p>

          <h4>9. Service Availability</h4>
          <p>We will endeavor to ensure that the Service is available 24 hours a day, but we shall not be liable if for any reason the Service is unavailable at any time or for any period. Access to the Service may be suspended temporarily and without notice in the case of system failure, maintenance, or repair, or for reasons beyond our control.</p>
          
          <h4>10. Disclaimer of Warranties</h4>
          <p>THE SERVICE IS PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS. YOUR USE OF THE SERVICE IS AT YOUR SOLE RISK. EDUCONNECT EXPRESSLY DISCLAIMS ALL WARRANTIES OF ANY KIND, WHETHER EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. WE DO NOT WARRANT THAT THE SERVICE WILL MEET YOUR SPECIFIC REQUIREMENTS OR THAT THE SERVICE WILL BE UNINTERRUPTED, TIMELY, SECURE, OR ERROR-FREE.</p>
          
          <h4>11. Limitation of Liability</h4>
          <p>IN NO EVENT SHALL EDUCONNECT, NOR ITS DIRECTORS, EMPLOYEES, PARTNERS, AGENTS, SUPPLIERS, OR AFFILIATES, BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL OR PUNITIVE DAMAGES, INCLUDING WITHOUT LIMITATION, LOSS OF PROFITS, DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES, RESULTING FROM YOUR ACCESS TO OR USE OF OR INABILITY TO ACCESS OR USE THE SERVICE.</p>

          <h4>12. Following Your Learning Plan</h4>
          <p>The personalized learning paths generated by our system are recommendations based on the data from your quiz performance. For the best results, we strongly encourage you to engage with the suggested materials and complete quizzes regularly as recommended by your personalized plan. Consistent and honest effort is the key to academic improvement.</p>
          
          <h4>13. Changes to Terms</h4>
          <p>We reserve the right, at our sole discretion, to modify or replace these Terms at any time. If a revision is material, we will make reasonable efforts to provide at least 30 days' notice prior to any new terms taking effect. What constitutes a material change will be determined at our sole discretion.</p>
          
        </div>
        <div className={styles.modalFooter}>
          <button onClick={onClose} className={styles.acceptButton}>I Understand</button>
        </div>
      </div>
    </div>
  );
};

export default PrivacyModal;