// In frontend/src/App.js
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SignUp from './pages/SignUp';
import Login from './pages/Login';
import LandingPage from './pages/LandingPage';
import SubjectPage from './pages/SubjectPage';
import QuizSelectionPage from './pages/QuizSelectionPage';
import QuizPage from './pages/QuizPage';
import PreQuizPage from './pages/PreQuizPage'; // <-- IMPORT THE NEW PAGE
import StudyMaterialsPage from './pages/StudyMaterialsPage'; // Import the new page
import PdfViewerPage from './pages/PdfViewerPage';
import PerformancePage from './pages/PerformancePage';
import UnitHistoryPage from './pages/UnitHistoryPage';
import PerformanceDashboard from './pages/PerformanceDashboard';
import DeepAnalysisPage from './pages/DeepAnalysisPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/login" element={<Login />} />
        <Route path="/subject/:subjectName" element={<SubjectPage />} />
        <Route path="/subject/:subjectName/quizzes" element={<QuizSelectionPage />} />
        <Route path="/subject/:subjectName/materials" element={<StudyMaterialsPage />} />
        <Route path="/subject/:subjectName/materials/:fileName" element={<PdfViewerPage />} />
        <Route path="/subject/:subjectName/performance" element={<PerformancePage />} />
        <Route path="/subject/:subjectName/performance/:unitName" element={<UnitHistoryPage />} />
        <Route path="/subject/:subjectName/dashboard" element={<PerformanceDashboard />} />
        <Route path="/subject/:subjectName/deep-analysis" element={<DeepAnalysisPage />} />

        {/* --- START OF EDITS --- */}
        {/* The old /quiz/:type/:name route is now the welcome screen */}
        <Route path="/quiz/welcome/:type/:name" element={<PreQuizPage />} />
        {/* A new route to handle the actual quiz taking */}
        <Route path="/quiz/start/:type/:name" element={<QuizPage />} />
        {/* --- END OF EDITS --- */}
      </Routes>
    </Router>
  );
}

export default App;