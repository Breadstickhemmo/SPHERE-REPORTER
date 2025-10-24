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
  const [isLoading, setIsLoading] = useState(false);
  const [isCollecting, setIsCollecting] = useState(false);
  const [collectionStatusMsg, setCollectionStatusMsg] = useState('Ожидание запуска');

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isStatsLoading, setIsStatsLoading] = useState(false);

  const [lastFilters, setLastFilters] = useState<any>(null);
  const prevIsCollecting = useRef<boolean>(false);

  // Аналитика по найденным коммитам (фронт)
  const calculateStats = (commits: any[]): DashboardStats => {
    const total_commits = commits.length;
    const total_lines_changed = commits.reduce((acc, c) => acc + (c.added_lines || 0) + (c.deleted_lines || 0), 0);
    const contributors = Array.from(new Set(commits.map(c => c.author_name)));
    const active_contributors = contributors.length;
    const last_commit_date = commits.length > 0 ? commits[0].commit_date : null;
    // Топ 5 контрибьюторов
    const contribMap: Record<string, number> = {};
    commits.forEach(c => {
      if (!contribMap[c.author_name]) contribMap[c.author_name] = 0;
      contribMap[c.author_name]++;
    });
    const top_contributors = Object.entries(contribMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([author, commits]) => ({ author, commits }));
    // Активность по дням
    const activityMap: Record<string, number> = {};
    commits.forEach(c => {
      const date = c.commit_date.slice(0, 10);
      activityMap[date] = (activityMap[date] || 0) + 1;
    });
    const labels = Object.keys(activityMap).sort();
    const data = labels.map(l => activityMap[l]);
    return {
      summary: {
        total_commits,
        total_lines_changed,
        active_contributors,
        last_commit_date,
      },
      top_contributors,
      commit_activity: { labels, data },
    };
  };

  // Запрос коммитов по фильтрам
  const fetchFilteredCommits = useCallback(async (filters: any) => {
    setIsLoading(true);
    setIsStatsLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.project_key) params.append('project_key', filters.project_key);
      if (filters.repo_name) params.append('repo_name', filters.repo_name);
      if (filters.branch_name) params.append('branch_name', filters.branch_name);
      if (filters.target_email) params.append('author_email', filters.target_email);
      if (filters.since) params.append('since', filters.since);
      if (filters.until) params.append('until', filters.until);
      const res = await fetchWithAuth(`/api/data/commits?${params.toString()}`);
      if (!res.ok) throw new Error('Ошибка загрузки коммитов по фильтрам');
      const data = await res.json();
      setCommits(data);
      setStats(calculateStats(data));
    } catch (error: any) {
      toast.error(error.message || 'Не удалось загрузить коммиты по фильтрам');
      setCommits([]);
      setStats(null);
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
    if (prevIsCollecting.current && !isCollecting && lastFilters) {
      toast.info("Сбор данных завершен, обновляем найденные коммиты...");
      fetchFilteredCommits(lastFilters);
    }
    prevIsCollecting.current = isCollecting;
  }, [isCollecting, fetchFilteredCommits, lastFilters]);

  useEffect(() => {
    const interval = setInterval(checkCollectionStatus, 5000);
    return () => clearInterval(interval);
  }, [checkCollectionStatus]);

  const handleStartAnalysis = async (params: any) => {
    setIsCollecting(true);
    setCollectionStatusMsg("Запрос на анализ отправлен...");
    toast.info("Запрос на анализ данных отправлен...");
    setLastFilters(params);
    setCommits([]);
    setStats(null);
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
    <div className="data-table">
        <h3>{title}</h3>
        <div className="table-wrapper">
            <table>
                <thead>
                    <tr>{headers.map((h: string) => <th key={h}>{h}</th>)}</tr>
                </thead>
                <tbody>
                    {isLoading && <tr><td colSpan={headers.length}>Загрузка...</td></tr>}
                    {!isLoading && data.length === 0 && <tr><td colSpan={headers.length}>Нет данных для анализа. Заполните форму выше.</td></tr>}
                    {!isLoading && data.map(renderRow)}
                </tbody>
            </table>
        </div>
    </div>
  );

  return (
    <div className="dashboard-container">
      <div className="analysis-section">
        <div className="content-wrapper">
            <div className="analysis-header">
                <h2>Введите данные для формирования отчета</h2>
                <div className="status-indicator">
                    <strong>Статус:</strong> {collectionStatusMsg}
                </div>
            </div>
            <AnalysisFilters 
                fetchWithAuth={fetchWithAuth} 
                onAnalysisStart={handleStartAnalysis} 
                isCollecting={isCollecting} 
            />
        </div>
      </div>

      <div className="results-section">
        <div className="content-wrapper">
            <Table
              title="Найденные коммиты по фильтрам"
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
            
            {stats && stats.summary.total_commits > 0 && (
                <div className="metrics-section card">
                    <h3>Аналитика по найденным коммитам</h3>
                    <MetricsDashboard stats={stats} isLoading={isStatsLoading} />
                </div>
            )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;