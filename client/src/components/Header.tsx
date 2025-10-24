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
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="22px" height="22px">
        <path d="M10 17.25V14H6v-4h4V6.75L15.25 12 10 17.25zM19 3H5c-1.1 0-2 .9-2 2v4h2V5h14v14H5v-4H3v4c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/>
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
      <div className="content-wrapper"> {/* <-- ИЗМЕНЕНИЕ: добавили wrapper */}
        <div className="logo">
          <img src={logo} alt="T1 Coding Report Logo" />
          {/* Текстовая надпись удалена, так как она теперь часть изображения */}
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