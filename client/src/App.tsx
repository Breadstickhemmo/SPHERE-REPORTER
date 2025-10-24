import React, { useEffect, useState, useCallback } from 'react';
import './styles/global.css';
import 'react-toastify/dist/ReactToastify.css';
import Header from './components/Header';
import AuthModal from './components/AuthModal';
import WelcomePage from './components/WelcomePage';
import Dashboard from './components/Dashboard';
import { ToastContainer, toast } from 'react-toastify';
import { fetchWithAuth as fetchWithAuthHelper } from './utils/fetchWithAuth';

interface User {
    id: number;
    username: string;
    email: string;
}

const App = () => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [authToken, setAuthToken] = useState<string | null>(null);
    const [currentUser, setCurrentUser] = useState<User | null>(null);
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
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    }
                    return null;
                })
                .then(data => {
                    if (data && data.user) {
                        setCurrentUser(data.user);
                        setIsAuthenticated(true);
                    }
                })
                .catch(err => {
                    if (!(err instanceof Error && err.message.includes('401'))) {
                        console.error("Ошибка проверки сессии:", err);
                    }
                })
                .finally(() => {
                    setAuthLoading(false);
                });
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
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка регистрации');
        }
        setIsRegisterOpen(false);
        toast.success(data.message || 'Регистрация прошла успешно!');
        setIsLoginOpen(true);
    };

    const handleLogin = async (formData: Record<string, string>) => {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка входа');
        }
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
                      <Dashboard fetchWithAuth={fetchWithAuth} />
                  </div>
              ) : (
                  <WelcomePage />
              )}
          </main>

          <AuthModal 
            isOpen={isRegisterOpen} 
            onClose={() => setIsRegisterOpen(false)} 
            onSubmit={handleRegister} 
            title="Регистрация" 
            submitButtonText="Зарегистрироваться" 
          />
          
          <AuthModal 
            isOpen={isLoginOpen} 
            onClose={() => setIsLoginOpen(false)} 
            onSubmit={handleLogin} 
            title="Вход" 
            submitButtonText="Войти" 
          />

          <ToastContainer 
            position="bottom-right" 
            autoClose={5000} 
            hideProgressBar={false} 
            theme="colored" 
          />
      </>
    );
};

export default App;