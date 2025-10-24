import React, { useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'react-toastify';
import AnalysisFilters from './AnalysisFilters';
import MetricsDashboard from './MetricsDashboard';
import '../styles/Dashboard.css';

interface DashboardProps {
  fetchWithAuth: (url: string, options?: RequestInit) => Promise<Response>;
}

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

const Dashboard: React.FC<DashboardProps> = ({ fetchWithAuth }) => {
  const [commits, setCommits] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCollecting, setIsCollecting] = useState(false);
  const [collectionStatusMsg, setCollectionStatusMsg] = useState('Ожидание запуска');

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isStatsLoading, setIsStatsLoading] = useState(true);

  const prevIsCollecting = useRef<boolean>(false);

  const fetchDashboardData = useCallback(async () => {
    setIsStatsLoading(true);
    try {
      const [statsRes, commitRes] = await Promise.all([
        fetchWithAuth('/api/metrics/dashboard_stats'),
        fetchWithAuth('/api/data/commits'),
      ]);
      
      if (!statsRes.ok) throw new Error('Ошибка загрузки статистики');
      if (!commitRes.ok) throw new Error('Ошибка загрузки коммитов');

      setStats(await statsRes.json());
      setCommits(await commitRes.json());

    } catch (error: any) {
      toast.error(error.message || 'Не удалось загрузить данные дашборда');
    } finally {
      setIsLoading(false);
      setIsStatsLoading(false);
    }
  }, [fetchWithAuth]);

  const checkCollectionStatus = useCallback(async () => {
    try {
      const res = await fetchWithAuth('/api/admin/collection-status');
      const data = await res.json();
      setIsCollecting(data.is_running);
      setCollectionStatusMsg(data.message);
    } catch (error) {
      console.error("Не удалось проверить статус сборщика", error);
    }
  }, [fetchWithAuth]);

  useEffect(() => {
    if (prevIsCollecting.current && !isCollecting) {
      toast.info("Сбор данных завершен, обновляем дашборд...");
      fetchDashboardData();
    }
    prevIsCollecting.current = isCollecting;
  }, [isCollecting, fetchDashboardData]);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(checkCollectionStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchDashboardData, checkCollectionStatus]);

  const handleStartAnalysis = async (params: any) => {
    setIsCollecting(true);
    setCollectionStatusMsg("Запрос на анализ отправлен...");
    toast.info("Запрос на анализ данных отправлен...");
    try {
      const response = await fetchWithAuth('/api/admin/start-collection', {
        method: 'POST',
        body: JSON.stringify(params),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message || 'Не удалось запустить анализ');
      }
      toast.success("Анализ запущен в фоновом режиме.");
    } catch (error: any) {
      toast.error(error.message);
      setIsCollecting(false);
    }
  };

  const Table = ({ title, headers, data, renderRow }: any) => (
    <div className="data-table card">
        <h3>{title} ({data.length})</h3>
        <div className="table-wrapper">
            <table>
                <thead>
                    <tr>{headers.map((h: string) => <th key={h}>{h}</th>)}</tr>
                </thead>
                <tbody>
                    {isLoading && <tr><td colSpan={headers.length}>Загрузка...</td></tr>}
                    {!isLoading && data.length === 0 && <tr><td colSpan={headers.length}>Нет данных</td></tr>}
                    {!isLoading && data.map(renderRow)}
                </tbody>
            </table>
        </div>
    </div>
  );

  return (
    <div>
      <div className="dashboard-header">
        <h2>Интерактивный анализ репозиториев</h2>
        <div className="status-indicator">
            <strong>Статус:</strong> {collectionStatusMsg}
        </div>
      </div>
      
      {/* --- БЛОК С МЕТРИКАМИ --- */}
      <div className="metrics-section">
        <h3>Общая аналитика по базе данных</h3>
        <MetricsDashboard stats={stats} isLoading={isStatsLoading} />
      </div>
      
      <hr className="divider" />

      {/* --- БЛОК С ФИЛЬТРАМИ ДЛЯ СБОРА ДАННЫХ --- */}
      <AnalysisFilters 
        fetchWithAuth={fetchWithAuth} 
        onAnalysisStart={handleStartAnalysis} 
        isCollecting={isCollecting} 
      />
      
      <div className="dashboard-grid" style={{ marginTop: '2rem' }}>
        <Table
          title="Последние 100 коммитов в БД"
          headers={['SHA', 'Автор', 'Сообщение', 'Дата']}
          data={commits}
          renderRow={(c: any) => (
            <tr key={c.sha}>
              <td title={c.sha}>{c.sha.substring(0, 7)}</td>
              <td>{c.author_name}</td>
              <td title={c.message}>{c.message}</td>
              <td>{new Date(c.commit_date).toLocaleString('ru-RU')}</td>
            </tr>
          )}
        />
      </div>
    </div>
  );
};

export default Dashboard;