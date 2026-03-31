"use client";

import { Settings, ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function ManufacturingPage() {
  const router = useRouter();

  return (
    <div style={{ padding: '2rem' }}>
      <button 
        onClick={() => router.back()}
        style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '0.5rem', 
          color: 'var(--text-secondary)',
          marginBottom: '2rem',
          background: 'none',
          border: 'none',
          cursor: 'pointer'
        }}
      >
        <ArrowLeft size={18} />
        Back to Launcher
      </button>

      <div className="card" style={{ padding: '4rem', textAlign: 'center', maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ 
          width: '80px', 
          height: '80px', 
          borderRadius: '1.5rem', 
          backgroundColor: 'rgba(100, 116, 139, 0.1)', 
          color: '#64748b',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 2rem'
        }}>
          <Settings size={40} />
        </div>
        
        <h1 className="heading-1" style={{ marginBottom: '1rem' }}>Manufacturing (MRP)</h1>
        <p className="text-muted" style={{ fontSize: '1.1rem', marginBottom: '2rem' }}>
          Bills of Materials (BOM), Work Orders, and production tracking.
        </p>
        
        <div style={{ 
          padding: '2rem', 
          border: '2px dashed var(--border-color)', 
          borderRadius: '1rem',
          color: 'var(--text-tertiary)'
        }}>
          Module views (BOMs, Work Centers, Production Orders) are under construction.
        </div>
      </div>
    </div>
  );
}
