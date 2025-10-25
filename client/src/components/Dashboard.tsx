import React, { useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'react-toastify';
import AnalysisFilters from './AnalysisFilters';
import MetricsDashboard from './MetricsDashboard';
import CommitDetailModal from './CommitDetailModal';
import HotspotsChart from './HotspotsChart';
import TemporalHeatmap from './TemporalHeatmap';
import '../styles/Dashboard.css';

interface DashboardProps {
  fetchWithAuth: (url: string, options?: RequestInit) => Promise<Response>;
}

interface TopContributor {
  author: string;
  average_kpi: number;
  commits: number;
}

interface DashboardStats {
  summary: {
    total_commits: number;
    total_lines_changed: number;
    active_contributors: number;
    last_commit_date: string | null;
  };
  top_contributors: TopContributor[];
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
  const [stats, setStats] = useState<any | null>(null);
  const [isStatsLoading, setIsStatsLoading] = useState(false);
  const [lastFilters, setLastFilters] = useState<any>(null);
  const prevIsCollecting = useRef<boolean>(false);
  const [selectedCommit, setSelectedCommit] = useState<any | null>(null);
  const [hotspots, setHotspots] = useState<any[]>([]);
  const [temporalPatterns, setTemporalPatterns] = useState<any[]>([]);
  const [isExtraMetricsLoading, setIsExtraMetricsLoading] = useState(false);

  const fetchDashboardStats = useCallback(async (filters: any = {}) => {
    setIsStatsLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.project_key) params.append('project_key', filters.project_key);
      if (filters.repo_name) params.append('repo_name', filters.repo_name);
      if (filters.target_email) params.append('author_email', filters.target_email);
      if (filters.since) params.append('since', filters.since);
      if (filters.until) params.append('until', filters.until);
      
      const res = await fetchWithAuth(`/api/metrics/dashboard_stats?${params.toString()}`);
      if (!res.ok) throw new Error('Ошибка загрузки статистики');
      const data = await res.json();
      setStats(data);
    } catch (error: any) {
      toast.error(error.message || 'Не удалось загрузить статистику');
      setStats(null);
    } finally {
      setIsStatsLoading(false);
    }
  }, [fetchWithAuth]);

  const fetchFilteredCommits = useCallback(async (filters: any) => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.project_key) params.append('project_key', filters.project_key);
      if (filters.repo_name) params.append('repo_name', filters.repo_name);
      if (filters.target_email) params.append('author_email', filters.target_email);
      if (filters.since) params.append('since', filters.since);
      if (filters.until) params.append('until', filters.until);
      const res = await fetchWithAuth(`/api/data/commits?${params.toString()}`);
      if (!res.ok) throw new Error('Ошибка загрузки коммитов по фильтрам');
      const data = await res.json();
      setCommits(data);
    } catch (error: any) {
      toast.error(error.message || 'Не удалось загрузить коммиты по фильтрам');
      setCommits([]);
    } finally {
      setIsLoading(false);
    }
  }, [fetchWithAuth]);

  const fetchExtraMetrics = useCallback(async (filters: any) => {
    setIsExtraMetricsLoading(true);
    try {
        const params = new URLSearchParams();
        if (filters.project_key) params.append('project_key', filters.project_key);
        if (filters.repo_name) params.append('repo_name', filters.repo_name);
        if (filters.target_email) params.append('author_email', filters.target_email);
        if (filters.since) params.append('since', filters.since);
        if (filters.until) params.append('until', filters.until);

        const [hotspotsRes, temporalRes] = await Promise.all([
            fetchWithAuth(`/api/metrics/hotspots?${params.toString()}`),
            fetchWithAuth(`/api/metrics/temporal_patterns?${params.toString()}`)
        ]);

        if (!hotspotsRes.ok) throw new Error('Ошибка загрузки горячих точек');
        const hotspotsData = await hotspotsRes.json();
        setHotspots(hotspotsData);

        if (!temporalRes.ok) throw new Error('Ошибка загрузки временных паттернов');
        const temporalData = await temporalRes.json();
        setTemporalPatterns(temporalData);

    } catch (error: any) {
        toast.error(error.message);
    } finally {
        setIsExtraMetricsLoading(false);
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
      toast.info("Сбор данных завершен, обновляем данные...");
      fetchFilteredCommits(lastFilters);
      fetchDashboardStats(lastFilters);
      fetchExtraMetrics(lastFilters);
    }
    prevIsCollecting.current = isCollecting;
  }, [isCollecting, fetchFilteredCommits, fetchDashboardStats, fetchExtraMetrics, lastFilters]);

  useEffect(() => {
    const interval = setInterval(checkCollectionStatus, 5000);
    fetchDashboardStats();
    return () => clearInterval(interval);
  }, [checkCollectionStatus, fetchDashboardStats]);

  const handleStartAnalysis = async (params: any) => {
    setIsCollecting(true);
    setCollectionStatusMsg("Запрос на анализ отправлен...");
    toast.info("Запрос на анализ данных отправлен...");
    setLastFilters(params);
    setCommits([]);
    setStats(null);
    setHotspots([]);
    setTemporalPatterns([]);

    fetchFilteredCommits(params);
    fetchDashboardStats(params);
    fetchExtraMetrics(params);
    
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
              headers={['Автор', 'Сообщение', 'Дата', 'Общая оценка', 'Действия']}
              data={commits}
              renderRow={(c: any) => (
                <tr key={c.sha}>
                  <td>{c.author_name}</td>
                  <td title={c.message}>{c.message}</td>
                  <td>{new Date(c.commit_date).toLocaleString('ru-RU')}</td>
                  <td>
                    {c.total_score_100 !== null && c.total_score_100 !== undefined ? `${c.total_score_100} / 100` : 'Нет оценки'}
                  </td>
                  <td>
                    <button 
                      className="secondary-btn" 
                      onClick={() => setSelectedCommit(c)}
                      disabled={c.total_score_100 === null || c.total_score_100 === undefined}
                    >
                      Детально
                    </button>
                  </td>
                </tr>
              )}
            />
            
            <div className="metrics-section card">
                <h3>Аналитика по найденным коммитам</h3>
                <MetricsDashboard stats={stats} isLoading={isStatsLoading} />
            </div>

            {isExtraMetricsLoading ? 
                <div className="loading-screen">Загрузка дополнительной аналитики...</div> :
                <>
                    <div className="additional-metric-wrapper">
                        <HotspotsChart data={hotspots} />
                    </div>
                    <div className="additional-metric-wrapper">
                        <TemporalHeatmap data={temporalPatterns} />
                    </div>
                </>
            }
        </div>
      </div>
      {selectedCommit && (
        <CommitDetailModal 
          commitSha={selectedCommit.sha}
          fetchWithAuth={fetchWithAuth}
          onClose={() => setSelectedCommit(null)}
        />
      )}
    </div>
  );
};

export default Dashboard;