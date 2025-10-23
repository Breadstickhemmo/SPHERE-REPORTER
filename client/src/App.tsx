import React, { useEffect, useState, useCallback } from 'react';
import './App.css';
import 'react-toastify/dist/ReactToastify.css';
import Header from './components/Header';
import AuthModal from './components/AuthModal';
import WelcomePage from './components/WelcomePage';
import { ToastContainer, toast } from 'react-toastify';
import { fetchWithAuth as fetchWithAuthHelper } from './utils/fetchWithAuth';

const App = () => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [authToken, setAuthToken] = useState<string | null>(null);
    const [currentUser, setCurrentUser] = useState<any>(null);
    const [authLoading, setAuthLoading] = useState<boolean>(true);
    const [isRegisterOpen, setIsRegisterOpen] = useState(false);
    const [isLoginOpen, setIsLoginOpen] = useState(false);

    const handleLogout = useCallback(() => {
        localStorage.removeItem('authToken');
        setAuthToken(null);
        setCurrentUser(null);
        setIsAuthenticated(false);
        toast.info("Вы вышли из системы.");
    }, []);

    const fetchWithAuth = useCallback(async (url: string, options: RequestInit = {}) => {
        try {
            return await fetchWithAuthHelper(url, options, handleLogout);
        } catch (error) {
            throw error;
        }
    }, [handleLogout]);

    useEffect(() => {
        const tokenFromStorage = localStorage.getItem('authToken');
        if (tokenFromStorage) {
            setAuthToken(tokenFromStorage);
        } else {
            setAuthLoading(false);
        }
    }, []);
    
    useEffect(() => {
        if (authToken) {
            setAuthLoading(true);
            fetchWithAuth('/api/me')
                .then(response => response.ok ? response.json() : null)
                .then(data => {
                    if (data) {
                        setCurrentUser(data.user);
                        setIsAuthenticated(true);
                    }
                })
                .catch(err => console.error("Ошибка проверки сессии:", err))
                .finally(() => setAuthLoading(false));
        } else {
            setIsAuthenticated(false);
            setAuthLoading(false);
        }
    }, [authToken, fetchWithAuth]);

    const handleRegister = async (formData: Record<string, string>) => {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Ошибка регистрации');
        setIsRegisterOpen(false);
        toast.success(data.message || 'Регистрация успешна!');
        setIsLoginOpen(true);
    };

    const handleLogin = async (formData: Record<string, string>) => {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Ошибка входа');
        localStorage.setItem('authToken', data.access_token);
        setAuthToken(data.access_token);
        setIsLoginOpen(false);
        toast.success(`Добро пожаловать, ${data.user.username}!`);
    };

    if (authLoading) {
        return <div className="loading-screen">Проверка авторизации...</div>;
    }

    return (
      <>
          <Header
              isAuthenticated={isAuthenticated}
              user={currentUser}
              onLoginClick={() => setIsLoginOpen(true)}
              onRegisterClick={() => setIsRegisterOpen(true)}
              onLogoutClick={handleLogout}
          />

          <main>
              {isAuthenticated ? (
                  <div className="content-wrapper">
                      <div className="card">
                          <h2>Дашборд эффективности</h2>
                          <p>Здесь будут метрики и графики.</p>
                      </div>
                  </div>
              ) : (
                  <WelcomePage />
              )}
          </main>

          <AuthModal isOpen={isRegisterOpen} onClose={() => setIsRegisterOpen(false)} onSubmit={handleRegister} title="Регистрация" submitButtonText="Зарегистрироваться" />
          <AuthModal isOpen={isLoginOpen} onClose={() => setIsLoginOpen(false)} onSubmit={handleLogin} title="Вход" submitButtonText="Войти" />

          <ToastContainer position="bottom-right" autoClose={5000} hideProgressBar={false} theme="colored" />
      </>
    );
};

export default App;