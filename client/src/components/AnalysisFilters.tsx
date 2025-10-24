import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-toastify';
import '../styles/AnalysisFilters.css';

interface AnalysisFiltersProps {
  fetchWithAuth: (url: string, options?: RequestInit) => Promise<Response>;
  onAnalysisStart: (params: any) => void;
  isCollecting: boolean;
}

const AnalysisFilters: React.FC<AnalysisFiltersProps> = ({ fetchWithAuth, onAnalysisStart, isCollecting }) => {
  const [projects, setProjects] = useState<any[]>([]);
  const [repositories, setRepositories] = useState<any[]>([]);
  const [branches, setBranches] = useState<any[]>([]);
  
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  const [isLoadingRepos, setIsLoadingRepos] = useState(false);
  const [isLoadingBranches, setIsLoadingBranches] = useState(false);

  const [selectedProject, setSelectedProject] = useState('');
  const [selectedRepo, setSelectedRepo] = useState('');
  const [selectedBranch, setSelectedBranch] = useState('');
  
  const [sferaUsername, setSferaUsername] = useState(() => localStorage.getItem('sfera_username') || '');
  const [sferaPassword, setSferaPassword] = useState(() => localStorage.getItem('sfera_password') || '');
  const [targetEmail, setTargetEmail] = useState(() => localStorage.getItem('target_email') || '');
  
  const today = new Date();
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(today.getDate() - 7);

  const [since, setSince] = useState(sevenDaysAgo.toISOString().split('T')[0]);
  const [until, setUntil] = useState(today.toISOString().split('T')[0]);

  const handleLoadProjects = async () => {
    if (!sferaUsername || !sferaPassword) {
      toast.error("Пожалуйста, введите Email и Пароль для 'Сферы'");
      return;
    }
    setIsLoadingProjects(true);
    setProjects([]);
    setSelectedProject('');
    try {
      const res = await fetchWithAuth('/api/sfera/projects', {
        method: 'POST',
        body: JSON.stringify({ sfera_username: sferaUsername, sfera_password: sferaPassword }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Ошибка загрузки проектов");
      
      setProjects(data);
      if (data.length > 0) {
        toast.success(`Загружено ${data.length} проектов`);
      } else {
        toast.warn("Проекты не найдены. Проверьте права доступа.");
      }
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setIsLoadingProjects(false);
    }
  };

  const fetchRepos = useCallback(async (projectKey: string) => {
    if (!projectKey || !sferaUsername || !sferaPassword) return;
    setIsLoadingRepos(true);
    try {
      const res = await fetchWithAuth('/api/sfera/repositories', {
        method: 'POST',
        body: JSON.stringify({ sfera_username: sferaUsername, sfera_password: sferaPassword, project_key: projectKey }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Ошибка загрузки репозиториев");
      setRepositories(data);
    } catch (error: any) {
      toast.error(error.message);
      setRepositories([]);
    } finally {
      setIsLoadingRepos(false);
    }
  }, [fetchWithAuth, sferaUsername, sferaPassword]);

  const fetchBranches = useCallback(async (projectKey: string, repoName: string) => {
    if (!projectKey || !repoName || !sferaUsername || !sferaPassword) return;
    setIsLoadingBranches(true);
    try {
      const res = await fetchWithAuth('/api/sfera/branches', {
        method: 'POST',
        body: JSON.stringify({ sfera_username: sferaUsername, sfera_password: sferaPassword, project_key: projectKey, repo_name: repoName }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Ошибка загрузки веток");
      setBranches(data);
    } catch (error: any) {
      toast.error(error.message);
      setBranches([]);
    } finally {
      setIsLoadingBranches(false);
    }
  }, [fetchWithAuth, sferaUsername, sferaPassword]);


  useEffect(() => {
    setRepositories([]);
    setSelectedRepo('');
    if (selectedProject) {
      fetchRepos(selectedProject);
    }
  }, [selectedProject, fetchRepos]);

  useEffect(() => {
    setBranches([]);
    setSelectedBranch('');
    if (selectedProject && selectedRepo) {
      fetchBranches(selectedProject, selectedRepo);
    }
  }, [selectedProject, selectedRepo, fetchBranches]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAnalysisStart({
      sfera_username: sferaUsername,
      sfera_password: sferaPassword,
      project_key: selectedProject,
      repo_name: selectedRepo,
      branch_name: selectedBranch,
      since: new Date(since).toISOString(),
      until: new Date(new Date(until).setHours(23, 59, 59, 999)).toISOString(),
      target_email: targetEmail.trim() || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="analysis-filters">
      <div className="filters-grid credentials-grid">
        <div className="form-group">
          <label>Email в Сфере</label>
          <input 
            type="text" 
            value={sferaUsername} 
            onChange={e => {
              setSferaUsername(e.target.value);
              localStorage.setItem('sfera_username', e.target.value);
            }} 
            className="form-control"
            required 
          />
        </div>
        <div className="form-group">
          <label>Пароль/Токен в Сфере</label>
          <input 
            type="password" 
            value={sferaPassword} 
            onChange={e => {
              setSferaPassword(e.target.value);
              localStorage.setItem('sfera_password', e.target.value);
            }}
            className="form-control" 
            required 
          />
        </div>
        <div className="form-group submit-group credentials-btn-group">
           <button type="button" className="secondary-btn" onClick={handleLoadProjects} disabled={isLoadingProjects}>
            {isLoadingProjects ? 'Загрузка...' : 'Загрузить проекты'}
          </button>
        </div>
      </div>
      
      <hr className="divider" />

      <div className="filters-grid">
        <div className="form-group">
          <label>Проект</label>
          <select value={selectedProject} onChange={e => setSelectedProject(e.target.value)} required disabled={projects.length === 0}>
            <option value="" disabled>{projects.length === 0 ? "Сначала загрузите проекты" : "Выберите проект"}</option>
            {projects.map(p => <option key={p.key} value={p.key}>{p.name}</option>)}
          </select>
        </div>
        
        <div className="form-group">
          <label>Репозиторий</label>
          <select value={selectedRepo} onChange={e => setSelectedRepo(e.target.value)} required disabled={!selectedProject}>
            <option value="" disabled>{isLoadingRepos ? "Загрузка..." : "Выберите репозиторий"}</option>
            {repositories.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
          </select>
        </div>

        <div className="form-group">
          <label>Ветка</label>
          <select value={selectedBranch} onChange={e => setSelectedBranch(e.target.value)} required disabled={!selectedRepo}>
            <option value="" disabled>{isLoadingBranches ? "Загрузка..." : "Выберите ветку"}</option>
            <option value="all">Все ветки</option>
            {branches.map(b => <option key={b.name} value={b.name}>{b.name}</option>)}
          </select>
        </div>
        
        <div className="form-group">
          <label>Email пользователя</label>
          <input 
            type="email" 
            value={targetEmail} 
            onChange={e => setTargetEmail(e.target.value)}
            placeholder="Оставьте пустым для всех пользователей"
          />
        </div>

        <div className="form-group">
          <label>Дата с</label>
          <input type="date" value={since} onChange={e => setSince(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Дата по</label>
          <input type="date" value={until} onChange={e => setUntil(e.target.value)} required />
        </div>

        <div className="form-group submit-group">
          <button type="submit" className="primary-btn" disabled={isCollecting || !selectedBranch}>
            {isCollecting ? 'Идет анализ...' : 'Сформировать отчет'}
          </button>
        </div>
      </div>
    </form>
  );
};

export default AnalysisFilters;