"use client";

import { useRouter } from 'next/navigation';
import { 
  Building2, 
  Users, 
  Wallet, 
  Package, 
  ShoppingCart, 
  HardHat, 
  GraduationCap,
  Calendar,
  Monitor,
  Settings
} from 'lucide-react';

const APPS = [
  { 
    name: 'POS', 
    description: 'Point of Sale',
    icon: Monitor, 
    path: '/dashboard/pos',
    color: '#6366f1',
    bgColor: 'rgba(99, 102, 241, 0.1)'
  },
  { 
    name: 'Sales', 
    description: 'Quotes and Orders',
    icon: ShoppingCart, 
    path: '/dashboard/sales',
    color: '#0ea5e9',
    bgColor: 'rgba(14, 165, 233, 0.1)'
  },
  { 
    name: 'CRM', 
    description: 'Pipeline Strategy',
    icon: Users, 
    path: '/dashboard/crm',
    color: '#8b5cf6',
    bgColor: 'rgba(139, 92, 246, 0.1)'
  },
  { 
    name: 'Invoicing', 
    description: 'Billing & Payments',
    icon: Wallet, 
    path: '/dashboard/invoicing',
    color: '#f59e0b',
    bgColor: 'rgba(245, 158, 11, 0.1)'
  },
  { 
    name: 'Inventory', 
    description: 'Stock & Operations',
    icon: Building2, 
    path: '/dashboard/inventory',
    color: '#10b981',
    bgColor: 'rgba(16, 185, 129, 0.1)'
  },
  { 
    name: 'Purchase', 
    description: 'Vendor Logistics',
    icon: Package, 
    path: '/dashboard/purchase',
    color: '#ec4899',
    bgColor: 'rgba(236, 72, 153, 0.1)'
  },
  { 
    name: 'Project', 
    description: 'Tasks & Timesheets',
    icon: HardHat, 
    path: '/dashboard/projects',
    color: '#f97316',
    bgColor: 'rgba(249, 115, 22, 0.1)'
  },
  { 
    name: 'Manufacturing', 
    description: 'BOMs & Work Orders',
    icon: Settings, 
    path: '/dashboard/manufacturing',
    color: '#64748b',
    bgColor: 'rgba(100, 116, 139, 0.1)'
  },
  { 
    name: 'eLearning', 
    description: 'Training Modules',
    icon: GraduationCap, 
    path: '/dashboard/elearning',
    color: '#84cc16',
    bgColor: 'rgba(132, 204, 22, 0.1)'
  },
  { 
    name: 'HR', 
    description: 'Time Off & Org',
    icon: Calendar, 
    path: '/dashboard/hr',
    color: '#14b8a6',
    bgColor: 'rgba(20, 184, 166, 0.1)'
  },
  { 
    name: 'Property', 
    description: 'Real Estate & Leasing',
    icon: Building2, 
    path: '/dashboard/property',
    color: '#f43f5e',
    bgColor: 'rgba(244, 63, 94, 0.1)'
  },
  { 
    name: 'School', 
    description: 'Students & Courses',
    icon: GraduationCap, 
    path: '/dashboard/school',
    color: '#22c55e',
    bgColor: 'rgba(34, 197, 94, 0.1)'
  },
];

export default function AppLauncher() {
  const router = useRouter();

  return (
    <div style={{ padding: '3rem 2rem', maxWidth: '1200px', margin: '0 auto' }}>
      
      <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
        <h1 className="heading-1" style={{ marginBottom: '0.5rem' }}>Welcome to your workspace</h1>
        <p className="text-muted" style={{ fontSize: '1.1rem' }}>Select an application to launch</p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
        gap: '2rem'
      }}>
        {APPS.map((app, index) => {
          const Icon = app.icon;
          
          return (
            <div 
              key={app.name}
              className="card animate-fade-in"
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center',
                padding: '2.5rem 1.5rem',
                cursor: 'pointer',
                border: '1px solid var(--border-color)',
                backgroundColor: 'var(--bg-secondary)',
                animationDelay: `${index * 0.05}s`,
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-5px) scale(1.02)';
                e.currentTarget.style.boxShadow = 'var(--shadow-lg)';
                e.currentTarget.style.borderColor = app.color;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0) scale(1)';
                e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
                e.currentTarget.style.borderColor = 'var(--border-color)';
              }}
              onClick={() => router.push(app.path)}
            >
              <div style={{
                width: '72px',
                height: '72px',
                borderRadius: '1.25rem',
                backgroundColor: app.bgColor,
                color: app.color,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.5rem',
                boxShadow: `0 8px 24px -6px ${app.color}40`,
                transition: 'transform 0.3s ease'
              }}>
                <Icon size={32} strokeWidth={2} />
              </div>
              
              <h3 style={{ 
                fontSize: '1.25rem', 
                fontWeight: 600, 
                color: 'var(--text-primary)',
                marginBottom: '0.5rem',
                letterSpacing: '-0.01em'
              }}>
                {app.name}
              </h3>
              
              <p style={{ 
                fontSize: '0.9rem', 
                color: 'var(--text-secondary)',
                lineHeight: 1.4
              }}>
                {app.description}
              </p>
            </div>
          );
        })}
      </div>
      
    </div>
  );
}
