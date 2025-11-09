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
import LearningSystem from './components/LearningSystem';
import AdminPanel from './components/AdminPanel';
import Materials from './components/Materials';
import PersonalDataForm from './components/PersonalDataForm';
import PersonalConsultations from './components/PersonalConsultations';
import CreditHistory from './components/CreditHistory';
import HomeContent from './components/HomeContent';
import PythagoreanSquareNew from './components/PythagoreanSquareNew';
import Settings from './components/Settings';

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
              <Route path="learning" element={<LearningSystem />} />
              <Route path="learning/lesson/:lessonId" element={<LearningSystem />} />
              <Route path="consultations" element={<PersonalConsultations />} />
              <Route path="report-export" element={<ReportExport />} />
              <Route path="materials" element={<Materials />} />
              <Route path="admin" element={<AdminPanel />} />
              <Route path="numerology-design" element={<PythagoreanSquareNew />} />
              <Route path="settings" element={<Settings />} />
            </Route>

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
