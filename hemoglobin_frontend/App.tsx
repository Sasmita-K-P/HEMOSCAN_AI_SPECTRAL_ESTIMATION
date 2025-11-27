
import React, { useState, useEffect } from 'react';
import Layout from './components/Layout';
import Home from './pages/Home';
import Scan from './pages/Scan';
import ClinicalDashboard from './components/ClinicalDashboard';
import History from './pages/History';
import Profile from './pages/Profile';
import Auth from './pages/Auth';
import { ViewState, AnalysisResult, User } from './types';
import { storageService } from './services/storage';

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [currentView, setCurrentView] = useState<ViewState>('HOME');
  const [history, setHistory] = useState<AnalysisResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<AnalysisResult | null>(null);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    const currentUser = storageService.getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
      const userHistory = storageService.getUserHistory(currentUser.id);
      setHistory(userHistory);
    }
    setIsLoadingAuth(false);
  }, []);

  const handleLogin = (loggedInUser: User) => {
    setUser(loggedInUser);
    // Load history for this specific user
    const userHistory = storageService.getUserHistory(loggedInUser.id);
    setHistory(userHistory);
    setCurrentView('HOME');
  };

  const handleLogout = () => {
    setUser(null);
    setHistory([]);
    setSelectedResult(null);
    setCurrentView('HOME');
  };

  const handleUserUpdate = (updatedUser: User) => {
    setUser(updatedUser);
  };

  const handleScanComplete = (result: AnalysisResult) => {
    if (!user) return;

    // Save to local state and "database"
    storageService.saveScan(user.id, result);
    setHistory((prev) => [...prev, result]);

    setSelectedResult(result);
    setCurrentView('RESULT');
  };

  const handleSelectFromHistory = (result: AnalysisResult) => {
    setSelectedResult(result);
    setCurrentView('RESULT');
  };

  const renderContent = () => {
    switch (currentView) {
      case 'HOME':
        return <Home onNavigate={setCurrentView} lastResult={history.length > 0 ? history[history.length - 1] : null} />;
      case 'SCAN':
        return <Scan onResult={handleScanComplete} onCancel={() => setCurrentView('HOME')} />;
      case 'RESULT':
        return selectedResult ? (
          <ClinicalDashboard
            result={selectedResult}
            onBack={() => setCurrentView('HOME')}
          />
        ) : (
          <Home onNavigate={setCurrentView} lastResult={null} />
        );
      case 'HISTORY':
        return <History history={history} onSelect={handleSelectFromHistory} />;
      case 'PROFILE':
        return user ? (
          <Profile user={user} onLogout={handleLogout} onUpdateUser={handleUserUpdate} />
        ) : null;
      default:
        return <Home onNavigate={setCurrentView} lastResult={null} />;
    }
  };

  if (isLoadingAuth) {
    return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-teal-600">Loading...</div>;
  }

  if (!user) {
    return <Auth onLogin={handleLogin} />;
  }

  return (
    <Layout currentView={currentView} onChangeView={setCurrentView}>
      {renderContent()}
    </Layout>
  );
};

export default App;
