import React from 'react';
import { useParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import styles from './PdfViewerPage.module.css';

const PdfViewerPage = () => {
  // --- This original code is untouched ---
  const { fileName } = useParams();
  // --- End of untouched original code ---
  
  // --- START OF NEW EDIT: Define and use API_URL ---
  const API_URL = process.env.REACT_APP_API_BASE_URL || '';
  const pdfUrl = `${API_URL}/api/v1/materials/download/${fileName}`;
  // --- END OF NEW EDIT ---
  
  // --- This original code is untouched ---
  const decodedName = decodeURIComponent(fileName).replace('.pdf', '').replace(/-/g, ' ');

  return (
    <>
      <Navbar />
      <div className={styles.pageWrapper}>
        <div className={styles.viewerHeader}>
          <h2>{decodedName}</h2>
          <a href={pdfUrl} download={fileName} className={styles.downloadButton}>
            Download PDF
          </a>
        </div>
        <div className={styles.pdfContainer}>
          <embed src={pdfUrl} type="application/pdf" width="100%" height="100%" />
          <p>Your browser does not support embedded PDFs. Please <a href={pdfUrl}>click here to download the PDF</a>.</p>
        </div>
      </div>
    </>
  );
  // --- End of untouched original code ---
};

export default PdfViewerPage;