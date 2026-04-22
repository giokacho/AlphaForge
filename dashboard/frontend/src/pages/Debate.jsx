import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import Skeleton from '../components/Skeleton';
import { TrendingUp, TrendingDown, Swords } from 'lucide-react';

const MONO = "'JetBrains Mono', 'Courier New', monospace";

const SectionLabel = ({ children, accentColor = '#ff6600' }) => (
  <div style={{
    color: accentColor,
    fontSize: '10px',
    fontWeight: '700',
    letterSpacing: '1.5px',
    borderBottom: `1px solid ${accentColor}33`,
    paddingBottom: '6px',
    marginBottom: '12px',
  }}>
    {children}
  </div>
);

export default function Debate() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/api/debate');
        setData(response.data);
      } catch (err) {
        console.error('Failed to load debate', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 180000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !data) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <Skeleton height="100px" borderRadius="0" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
          <Skeleton height="320px" borderRadius="0" />
          <Skeleton height="320px" borderRadius="0" />
          <Skeleton height="320px" borderRadius="0" />
        </div>
        <Skeleton height="120px" borderRadius="0" />
      </div>
    );
  }

  const direction = data.final_direction || 'NO_SIGNAL';
  const dColor = direction === 'LONG' ? '#00ff41' : direction === 'SHORT' ? '#ff3333' : '#444';
  const DirIcon = direction === 'LONG' ? TrendingUp : direction === 'SHORT' ? TrendingDown : Swords;

  const convScore = data.conviction_score || 0;
  const convPct = (convScore / 10) * 100;

  const panel = { border: '1px solid #222', backgroundColor: '#0d0d0d' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '16px' }}>
        <div style={{ color: '#ff6600', fontSize: '13px', fontWeight: '700', letterSpacing: '2px' }}>
          NEURAL SYNTHESIS BOARD
        </div>
        <div style={{ color: '#333', fontSize: '10px' }}>CIO-LEVEL DEBATE — BULL / BEAR / RISK SYNTHESIS</div>
      </div>

      {/* Final Verdict Panel */}
      <div style={{ ...panel, marginBottom: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: `1px solid ${dColor}33` }}>

        <div style={{ padding: '16px 20px', borderRight: '1px solid #222' }}>
          <div style={{ color: '#444', fontSize: '10px', letterSpacing: '1.5px', marginBottom: '10px' }}>FINAL VERDICT</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: dColor,
              fontSize: '28px',
              fontWeight: '700',
              fontFamily: MONO,
              padding: '6px 16px',
              border: `1px solid ${dColor}`,
              backgroundColor: `${dColor}0a`,
            }}>
              <DirIcon size={22} />
              {direction}
            </div>
          </div>
        </div>

        <div style={{ padding: '16px 20px' }}>
          <div style={{ color: '#444', fontSize: '10px', letterSpacing: '1.5px', marginBottom: '10px' }}>CONVICTION MODEL</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginBottom: '10px' }}>
            <span style={{ color: '#ff6600', fontSize: '36px', fontWeight: '700', fontFamily: MONO, lineHeight: 1 }}>
              {convScore}
            </span>
            <span style={{ color: '#333', fontSize: '18px', fontFamily: MONO }}>/10</span>
          </div>
          <div style={{ height: '4px', backgroundColor: '#111' }}>
            <div style={{ height: '100%', width: `${convPct}%`, backgroundColor: '#ff6600', transition: 'width 1s ease' }} />
          </div>
        </div>

      </div>

      {/* 3 Case Panels */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '12px' }}>

        {/* Bull Case */}
        <div style={{ ...panel, borderLeft: '2px solid #00ff41' }}>
          <div style={{ padding: '12px 14px' }}>
            <SectionLabel accentColor="#00ff41">STRUCTURAL BULL CASE</SectionLabel>
            <div style={{ color: '#555', fontSize: '11px', lineHeight: '1.7', whiteSpace: 'pre-wrap', fontFamily: MONO }}>
              {data.bull_case}
            </div>
          </div>
        </div>

        {/* Bear Case */}
        <div style={{ ...panel, borderLeft: '2px solid #ff3333' }}>
          <div style={{ padding: '12px 14px' }}>
            <SectionLabel accentColor="#ff3333">STRUCTURAL BEAR CASE</SectionLabel>
            <div style={{ color: '#555', fontSize: '11px', lineHeight: '1.7', whiteSpace: 'pre-wrap', fontFamily: MONO }}>
              {data.bear_case}
            </div>
          </div>
        </div>

        {/* Risk Case */}
        <div style={{ ...panel, borderLeft: '2px solid #ffaa00' }}>
          <div style={{ padding: '12px 14px' }}>
            <SectionLabel accentColor="#ffaa00">TAIL RISK CONSIDERATIONS</SectionLabel>
            <div style={{ color: '#555', fontSize: '11px', lineHeight: '1.7', whiteSpace: 'pre-wrap', fontFamily: MONO }}>
              {data.risk_case}
            </div>
          </div>
        </div>

      </div>

      {/* Synthesis */}
      <div style={{ ...panel, borderLeft: '2px solid #ff6600' }}>
        <div style={{ padding: '12px 16px' }}>
          <SectionLabel>FINAL STRATEGIC SYNTHESIS</SectionLabel>
          <div style={{ color: '#888', fontSize: '12px', lineHeight: '1.7', whiteSpace: 'pre-wrap', fontFamily: MONO }}>
            {data.synthesis}
          </div>
        </div>
      </div>

    </div>
  );
}
