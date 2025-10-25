import React from 'react';
import '../styles/TemporalHeatmap.css';

interface TemporalData {
  day: string;
  hour: number;
  commits: number;
}

interface TemporalHeatmapProps {
  data: TemporalData[];
}

const TemporalHeatmap: React.FC<TemporalHeatmapProps> = ({ data }) => {
  const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const maxCommits = Math.max(...data.map(d => d.commits), 0);

  const dataMap = new Map<string, number>();
  data.forEach(d => {
    dataMap.set(`${d.day}-${d.hour}`, d.commits);
  });

  const getColor = (commits: number) => {
    if (commits === 0) return 'rgba(47, 43, 240, 0.05)';
    const opacity = 0.1 + (commits / maxCommits) * 0.9;
    return `rgba(47, 43, 240, ${opacity})`;
  };

  return (
    <div className="heatmap-chart card">
      <h3>Временные паттерны (коммиты по дням и часам)</h3>
      <div className="heatmap-grid">
        <div className="heatmap-hours-labels">
          {hours.map(hour => (hour % 3 === 0 ? <div key={hour} className="hour-label">{`${hour}:00`}</div> : null))}
        </div>
        <div className="heatmap-body">
          <div className="heatmap-days-labels">
            {days.map(day => <div key={day} className="day-label">{day}</div>)}
          </div>
          <div className="heatmap-cells">
            {days.map(day => (
              <div key={day} className="heatmap-row">
                {hours.map(hour => {
                  const commits = dataMap.get(`${day}-${hour}`) || 0;
                  return (
                    <div
                      key={hour}
                      className="heatmap-cell"
                      style={{ backgroundColor: getColor(commits) }}
                      title={`${commits} коммитов в ${hour}:00-${hour}:59`}
                    ></div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TemporalHeatmap;