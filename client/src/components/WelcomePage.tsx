import '../styles/WelcomePage.css';

const CheckIcon = () => (
  <svg className="feature-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M20 6L9 17L4 12" stroke="#2F2BF0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const WelcomePage = () => {
  return (
    <div className="welcome-container">
      <section className="hero-section">
        <div className="content-wrapper">
            <h1>Добро пожаловать!</h1>
            <p>Войдите или зарегистрируйтесь, чтобы попробовать наш продукт</p>
        </div>
      </section>

      <section className="info-section">
        <div className="content-wrapper">
          <h2>Что это за приложение?</h2>
          <p>
            Это автоматизированная система анализа Git-репозиториев для роста вашей команды. Приложение помогает оценить эффективность работы каждого разработчика.
          </p>
        </div>
      </section>

      <section className="info-section">
        <div className="content-wrapper">
          <h3>Как это работает:</h3>
          <div className="features-grid">
            <div className="feature-item">
              <CheckIcon />
              <p>Система интегрируется с "Т1 Сфера.Код" для сбора данных об активности в репозиториях.</p>
            </div>
            <div className="feature-item">
              <CheckIcon />
              <p>Анализирует коммиты, ветки и изменения кода для выявления паттернов и аномалий.</p>
            </div>
            <div className="feature-item">
              <CheckIcon />
              <p>Вычисляет ключевые KPI для оценки производительности и стабильности кода.</p>
            </div>
            <div className="feature-item">
              <CheckIcon />
              <p>Предоставляет наглядные дашборды с рекомендациями для улучшения процессов разработки.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default WelcomePage;