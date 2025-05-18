import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styled from 'styled-components';

interface Alert {
  timestamp: string;
  risk_score: number;
  uv_value: number;
  pollen_value: number;
  message: string;
  severity: 'high' | 'moderate' | 'low';
}

const AlertContainer = styled.div`
  max-width: 600px;
  margin: 20px auto;
  padding: 20px;
`;

const AlertCard = styled(motion.div)<{ severity: string }>`
  background: ${props => {
    switch (props.severity) {
      case 'high':
        return 'linear-gradient(135deg, #ff4b4b 0%, #ff7676 100%)';
      case 'moderate':
        return 'linear-gradient(135deg, #ffa726 0%, #ffcc80 100%)';
      default:
        return 'linear-gradient(135deg, #66bb6a 0%, #a5d6a7 100%)';
    }
  }};
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const AlertHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
`;

const AlertTitle = styled.h3`
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
`;

const AlertTime = styled.span`
  font-size: 0.9rem;
  opacity: 0.9;
`;

const AlertContent = styled.div`
  font-size: 1rem;
  line-height: 1.5;
`;

const AlertMetrics = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 16px;
  background: rgba(255, 255, 255, 0.1);
  padding: 12px;
  border-radius: 8px;
`;

const Metric = styled.div`
  text-align: center;
`;

const MetricLabel = styled.div`
  font-size: 0.8rem;
  opacity: 0.9;
  margin-bottom: 4px;
`;

const MetricValue = styled.div`
  font-size: 1.2rem;
  font-weight: 600;
`;

const NoAlerts = styled.div`
  text-align: center;
  color: #666;
  padding: 40px;
  font-size: 1.1rem;
`;

const AlertDisplay: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await fetch('/data/alerts.json');
        const data = await response.json();
        setAlerts(data);
      } catch (error) {
        console.error('Error fetching alerts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    // Set up polling every 5 minutes
    const interval = setInterval(fetchAlerts, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  if (loading) {
    return <div>Loading alerts...</div>;
  }

  return (
    <AlertContainer>
      <AnimatePresence>
        {alerts.length > 0 ? (
          alerts.map((alert, index) => (
            <AlertCard
              key={alert.timestamp}
              severity={alert.severity}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
            >
              <AlertHeader>
                <AlertTitle>
                  {alert.severity === 'high' ? '⚠️ High Risk Alert' :
                   alert.severity === 'moderate' ? '⚠️ Moderate Risk Alert' :
                   'ℹ️ Low Risk Alert'}
                </AlertTitle>
                <AlertTime>{formatTime(alert.timestamp)}</AlertTime>
              </AlertHeader>
              
              <AlertContent>
                {alert.message}
              </AlertContent>

              <AlertMetrics>
                <Metric>
                  <MetricLabel>Risk Score</MetricLabel>
                  <MetricValue>{alert.risk_score.toFixed(1)}/10</MetricValue>
                </Metric>
                <Metric>
                  <MetricLabel>UV Index</MetricLabel>
                  <MetricValue>{alert.uv_value.toFixed(1)}</MetricValue>
                </Metric>
                <Metric>
                  <MetricLabel>Pollen Level</MetricLabel>
                  <MetricValue>{alert.pollen_value.toFixed(1)}</MetricValue>
                </Metric>
              </AlertMetrics>
            </AlertCard>
          ))
        ) : (
          <NoAlerts>
            No active alerts at this time. Conditions are safe for your profile.
          </NoAlerts>
        )}
      </AnimatePresence>
    </AlertContainer>
  );
};

export default AlertDisplay; 