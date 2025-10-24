import React from 'react';
import '../styles/MetricsDashboard.css';

interface DashboardStats {
  summary: {
    total_commits: number;
    total_lines_changed: number;
    active_contributors: number;
    last_commit_date: string | null;
  };
  top_contributors: {
    author: string;
    commits: number;
  }[];
  commit_activity: {
    labels: string[];
    data: number[];
  };
}

interface MetricsDashboardProps {
  stats: DashboardStats | null;
  isLoading: boolean;
}

const StatCard: React.FC<{ title: string; value: string | number, className?: string }> = ({ title, value, className }) => (
  <div className={`stat-card card ${className || ''}`}>
    <h4>{title}</h4>
    <p>{value}</p>
  </div>
);

const SimpleBarChart: React.FC<{ data: { label: string; value: number }[], title: string }> = ({ data, title }) => {
    const maxValue = Math.max(...data.map(d => d.value), 0);
    return (
        <div className="bar-chart card">
            <h3>{title}</h3>
            <div className="chart-area">
                {data.length > 0 ? data.map(item => (
                    <div className="bar-item" key={item.label}>
                        <div className="bar-label" title={item.label}>{item.label}</div>
                        <div className="bar-wrapper">
                            <div 
                                className="bar" 
                                style={{ width: `${maxValue > 0 ? (item.value / maxValue) * 100 : 0}%` }}
                                title={`Коммитов: ${item.value}`}
                            >
                            </div>
                        </div>
                         <div className="bar-value">{item.value}</div>
                    </div>
                )) : <p>Нет данных для отображения</p>}
            </div>
        </div>
    );
};


const MetricsDashboard: React.FC<MetricsDashboardProps> = ({ stats, isLoading }) => {
  if (isLoading) {
    return <div className="loading-screen">Загрузка аналитики...</div>;
  }

  if (!stats || stats.summary.total_commits === 0) {
    return (
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
            <h3>Данные для анализа отсутствуют</h3>
            <p>Чтобы начать, используйте форму ниже для сбора данных из вашего репозитория.</p>
        </div>
    );
  }

  const { summary, top_contributors } = stats;

  return (
    <div className="metrics-dashboard">
      <div className="stats-grid">
        <StatCard title="Всего коммитов" value={summary.total_commits.toLocaleString('ru-RU')} />
        <StatCard title="Всего строк изменено" value={summary.total_lines_changed.toLocaleString('ru-RU')} />
        <StatCard title="Активных контрибьюторов" value={summary.active_contributors} />
        <StatCard 
            title="Последний коммит" 
            value={summary.last_commit_date ? new Date(summary.last_commit_date).toLocaleDateString('ru-RU') : 'N/A'} 
        />
      </div>
      
      <div className="dashboard-grid" style={{ marginTop: '2rem' }}>
        <SimpleBarChart 
            title="Топ 5 контрибьюторов"
            data={top_contributors.map(c => ({ label: c.author, value: c.commits }))}
        />
      </div>
    </div>
  );
};

export default MetricsDashboard;