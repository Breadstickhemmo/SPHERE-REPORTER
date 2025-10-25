// src/components/UserAnalyticsDashboard.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-toastify';
import '../styles/UserAnalyticsDashboard.css';

interface UserAnalyticsProps {
  user: { name: string; email: string };
  filters: any;
  fetchWithAuth: (url: string, options?: RequestInit) => Promise<Response>;
}

const UserAnalyticsDashboard: React.FC<UserAnalyticsProps> = ({ user, filters, fetchWithAuth }) => {
  const [userData, setUserData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUserData = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('author_email', user.email);
      if (filters.project_key) params.append('project_key', filters.project_key);
      if (filters.repo_name) params.append('repo_name', filters.repo_name);
      if (filters.since) params.append('since', filters.since);
      if (filters.until) params.append('until', filters.until);

      const res = await fetchWithAuth(`/api/metrics/user_summary?${params.toString()}`);
      if (!res.ok) throw new Error('Не удалось загрузить персональную аналитику');
      const data = await res.json();
      setUserData(data);
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setIsLoading(false);
    }
  }, [user, filters, fetchWithAuth]);

  useEffect(() => {
    fetchUserData();
  }, [fetchUserData]);

  if (isLoading) {
    return <div className="user-analytics-card loading">Загрузка аналитики для {user.name}...</div>;
  }

  return (
    <div className="user-analytics-card">
      <h3>Персональная аналитика: {user.name}</h3>
      <div className="user-stats-grid">
        <div className="user-stat">
          <h4>Всего коммитов</h4>
          <p>{userData?.summary?.total_commits || 0}</p>
        </div>
        <div className="user-stat">
          <h4>Средний KPI</h4>
          <p>{userData?.summary?.average_kpi || 0} / 100</p>
        </div>
      </div>
      <h4>Сводные рекомендации</h4>
      <p className="recommendation-text">
        {userData?.recommendation || 'Нет рекомендаций.'}
      </p>
    </div>
  );
};

export default UserAnalyticsDashboard;