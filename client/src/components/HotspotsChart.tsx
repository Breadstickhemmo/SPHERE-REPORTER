import React from 'react';

interface Hotspot {
  file: string;
  changes: number;
}

interface HotspotsChartProps {
  data: Hotspot[];
}

const HotspotsChart: React.FC<HotspotsChartProps> = ({ data }) => {
  const maxValue = data.length > 0 ? Math.max(...data.map(d => d.changes)) : 0;
  return (
    <div className="bar-chart card">
      <h3>Горячие точки (Топ-10 изменяемых файлов)</h3>
      <div className="chart-area">
        {data.length > 0 ? data.map(item => (
          <div className="bar-item" key={item.file}>
            <div className="bar-label" title={item.file}>{item.file}</div>
            <div className="bar-wrapper">
              <div
                className="bar"
                style={{ width: `${maxValue > 0 ? (item.changes / maxValue) * 100 : 0}%` }}
                title={`Изменений: ${item.changes}`}
              ></div>
            </div>
            <div className="bar-value">{item.changes}</div>
          </div>
        )) : <p>Нет данных для отображения</p>}
      </div>
    </div>
  );
};

export default HotspotsChart;