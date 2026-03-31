"use client";

import { GraduationCap, ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function ELearningPage() {
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
          backgroundColor: 'rgba(132, 204, 22, 0.1)', 
          color: '#84cc16',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 2rem'
        }}>
          <GraduationCap size={40} />
        </div>
        
        <h1 className="heading-1" style={{ marginBottom: '1rem' }}>eLearning & Training</h1>
        <p className="text-muted" style={{ fontSize: '1.1rem', marginBottom: '2rem' }}>
          Course creation, employee training tracks, and certification management.
        </p>
        
        <div style={{ 
          padding: '2rem', 
          border: '2px dashed var(--border-color)', 
          borderRadius: '1rem',
          color: 'var(--text-tertiary)'
        }}>
          Module views (Courses, Lectures, Quizzes) are under construction.
        </div>
      </div>
    </div>
  );
}
