"use client";

import { GraduationCap, ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function SchoolPage() {
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
          backgroundColor: 'rgba(34, 197, 94, 0.1)', 
          color: '#22c55e',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 2rem'
        }}>
          <GraduationCap size={40} />
        </div>
        
        <h1 className="heading-1" style={{ marginBottom: '1rem' }}>School Management System</h1>
        <p className="text-muted" style={{ fontSize: '1.1rem', marginBottom: '2rem' }}>
          Student enrollment, academic courses, grading, and scheduling.
        </p>
        
        <div style={{ 
          padding: '2rem', 
          border: '2px dashed var(--border-color)', 
          borderRadius: '1rem',
          color: 'var(--text-tertiary)'
        }}>
          Module views (Students, Classes, Admissions) are under construction.
        </div>
      </div>
    </div>
  );
}
