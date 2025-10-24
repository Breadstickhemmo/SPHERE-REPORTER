import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import '../styles/AuthModal.css';
import '../styles/MetricsDashboard.css';

interface CommitDetailModalProps {
  commitSha: string;
  fetchWithAuth: (url: string, options?: RequestInit) => Promise<Response>;
  onClose: () => void;
}

interface CommitDetails {
  message: string;
  author_name: string;
  commit_date: string;
  llm_scores: {
    size: number;
    quality: number;
    complexity: number;
    comment: number;
  };
  llm_recommendations: string;
}

const ScoreCard: React.FC<{ title: string; value: number }> = ({ title, value }) => (
    <div className="stat-card card">
      <h4>{title}</h4>
      <p style={{ fontSize: '2rem' }}>{value !== null && value !== undefined ? `${value} / 5` : 'N/A'}</p>
    </div>
);

const CommitDetailModal: React.FC<CommitDetailModalProps> = ({ commitSha, fetchWithAuth, onClose }) => {
  const [details, setDetails] = useState<CommitDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDetails = async () => {
      setIsLoading(true);
      try {
        const res = await fetchWithAuth(`/api/data/commits/${commitSha}/details`);
        if (!res.ok) throw new Error('Не удалось загрузить детали коммита');
        const data = await res.json();
        setDetails(data);
      } catch (error: any) {
        toast.error(error.message);
        onClose();
      } finally {
        setIsLoading(false);
      }
    };
    if (commitSha) {
      fetchDetails();
    }
  }, [commitSha, fetchWithAuth, onClose]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '700px' }} onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} style={{ position: 'absolute', top: '10px', right: '10px', background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>
          &times;
        </button>
        <h2>Детальный анализ коммита</h2>
        {isLoading ? (
          <p>Загрузка деталей...</p>
        ) : details ? (
          <div>
            <p><strong>Автор:</strong> {details.author_name}</p>
            <p><strong>Дата:</strong> {new Date(details.commit_date).toLocaleString('ru-RU')}</p>
            <p><strong>Сообщение:</strong> {details.message}</p>
            
            <h3 style={{marginTop: '2rem'}}>Оценки GigaChat</h3>
            <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                <ScoreCard title="Размер" value={details.llm_scores.size} />
                <ScoreCard title="Качество" value={details.llm_scores.quality} />
                <ScoreCard title="Сложность" value={details.llm_scores.complexity} />
                <ScoreCard title="Комментарий" value={details.llm_scores.comment} />
            </div>

            <h3 style={{marginTop: '2rem'}}>Рекомендации и комментарии GigaChat</h3>
            <div className="card" style={{ background: '#f8f9fa', maxHeight: '200px', overflowY: 'auto' }}>
                <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: '0.9rem', margin: 0 }}>
                    {details.llm_recommendations}
                </pre>
            </div>
          </div>
        ) : (
          <p>Нет данных для отображения.</p>
        )}
      </div>
    </div>
  );
};

export default CommitDetailModal;