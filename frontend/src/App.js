import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";
import { AuthProvider } from "./components/AuthContext";
import MainDashboard from "./components/MainDashboard";
import UserDashboard from "./components/UserDashboard";
import PaymentSuccess from "./components/PaymentSuccess";
import PaymentCancelled from "./components/PaymentCancelled";

// Импорты для всех разделов
import NameNumerology from './components/NameNumerology';
import Compatibility from './components/CompatibilityNew';
import Quiz from './components/Quiz';
import PlanetaryDailyRoute from './components/PlanetaryDailyRouteNew';
import ReportExport from './components/ReportExport';
import VedicTimeCalculations from './components/VedicTimeCalculations';
import LearningSystemV2 from './components/LearningSystemV2';
import LearningV2Portal from './components/LearningV2Portal';
import AdminV2Portal from './components/AdminV2Portal';
import AdminPanel from './components/AdminPanel';
import AdminPanelV2 from './components/AdminPanelV2';
import UserDashboardV2 from './components/UserDashboardV2';
import MainDashboardV2 from './components/MainDashboardV2';
import AnalyticsDetailPage from './components/AnalyticsDetailPage';
import Materials from './components/Materials';
import PersonalDataForm from './components/PersonalDataForm';
import PersonalConsultations from './components/PersonalConsultations';
import CreditHistory from './components/CreditHistory';
import HomeContent from './components/HomeContent';
import PythagoreanSquareNew from './components/PythagoreanSquareNew';
import Settings from './components/Settings';
import ComprehensiveReport from './components/ComprehensiveReport';

function App() {
  return (
    <AuthProvider>
      <div className="App min-h-screen">
        <BrowserRouter>
          <Routes>
            {/* Главная - лендинг или дашборд */}
            <Route path="/" element={<MainDashboard />} />

            {/* Дашборд пользователя с вложенными роутами */}
            <Route path="/dashboard" element={<UserDashboard />}>
              <Route index element={<Navigate to="/dashboard/home" replace />} />
              <Route path="home" element={<HomeContent />} />
              <Route path="personal-data" element={<PersonalDataForm />} />
              <Route path="credit-history" element={<CreditHistory />} />
              <Route path="numerology" element={<Navigate to="/dashboard/numerology-design" replace />} />
              <Route path="name-numerology" element={<NameNumerology />} />
              <Route path="vedic-time" element={<VedicTimeCalculations />} />
              <Route path="planetary-route" element={<PlanetaryDailyRoute />} />
              <Route path="compatibility" element={<Compatibility />} />
              <Route path="quiz" element={<Quiz />} />
              <Route path="learning-v2" element={<LearningV2Portal />} />
              <Route path="admin-v2" element={<AdminV2Portal />} />
              <Route path="consultations" element={<PersonalConsultations />} />
              <Route path="report-export" element={<ReportExport />} />
              <Route path="materials" element={<Materials />} />
              <Route path="admin" element={<AdminPanel />} />
              <Route path="numerology-design" element={<PythagoreanSquareNew />} />
              <Route path="comprehensive-report" element={<ComprehensiveReport />} />
              <Route path="settings" element={<Settings />} />
            </Route>

            {/* Отдельная система обучения V2 */}
            <Route path="/learning-v2-dashboard" element={<UserDashboardV2 />} />
            <Route path="/learning-v2-lesson/:lessonId" element={<LearningSystemV2 />} />
            <Route path="/analytics/:section" element={<AnalyticsDetailPage />} />


            {/* Платежи */}
            <Route path="/payment-success" element={<PaymentSuccess />} />
            <Route path="/payment-cancelled" element={<PaymentCancelled />} />

            {/* 404 */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;
