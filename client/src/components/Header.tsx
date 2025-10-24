import React from 'react';
import logo from '../assets/logo-full.png';
import '../styles/Header.css';

interface User {
  id: number;
  username: string;
  email: string;
}

interface HeaderProps {
  isAuthenticated: boolean;
  user: User | null;
  onLoginClick: () => void;
  onRegisterClick: () => void;
  onLogoutClick: () => void;
}

const LogoutIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="22px" height="22px">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
        <polyline points="16 17 21 12 16 7"></polyline>
        <line x1="21" y1="12" x2="9" y2="12"></line>
    </svg>
);


const Header: React.FC<HeaderProps> = ({
  isAuthenticated,
  user,
  onLoginClick,
  onRegisterClick,
  onLogoutClick
}) => {
  return (
    <header className="header">
      <div className="content-wrapper">
        <div className="logo">
          <img src={logo} alt="T1 Coding Report Logo" />
        </div>
        <div className="auth-buttons">
          {isAuthenticated ? (
            <>
              <span className="welcome-user">
                  Привет, {user?.username || 'Пользователь'}!
              </span>
              <button
                className="logout-icon-btn"
                onClick={onLogoutClick}
                title="Выход"
                aria-label="Выход"
              >
                <LogoutIcon />
              </button>
            </>
          ) : (
            <>
              <button
                className="login-btn"
                onClick={onLoginClick}
              >
                Войти
              </button>
              <button
                className="register-btn"
                onClick={onRegisterClick}
              >
                Зарегистрироваться
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;