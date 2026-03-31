"use client";

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { 
  Building2, 
  Users, 
  Wallet, 
  Package, 
  ShoppingCart, 
  HardHat, 
  GraduationCap, 
  LogOut,
  Bell,
  Search,
  ChevronLeft,
  ChevronRight,
  Settings,
  MonitorSmartphone
} from 'lucide-react';
import api from '@/lib/api';
import ThemeToggle from '@/components/ThemeToggle';

const MODULES = [
  { name: 'Point of Sale', icon: MonitorSmartphone, path: '/dashboard/pos' },
  { name: 'CRM', icon: Users, path: '/dashboard/crm' },
  { name: 'Sales', icon: ShoppingCart, path: '/dashboard/sales' },
  { name: 'Products', icon: Package, path: '/dashboard/products' },
  { name: 'Inventory', icon: Building2, path: '/dashboard/inventory' },
  { name: 'Invoicing', icon: Wallet, path: '/dashboard/invoicing' },
  { name: 'Purchase', icon: Package, path: '/dashboard/purchase' },
  // Phase 4 Stubs:
  { name: 'Human Resources', icon: Users, path: '/dashboard/hr' },
  { name: 'Project Management', icon: HardHat, path: '/dashboard/projects' },
  { name: 'Manufacturing', icon: Building2, path: '/dashboard/manufacturing' },
  { name: 'eLearning', icon: GraduationCap, path: '/dashboard/elearning' },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState<any>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    // Basic Auth Check
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
    } else {
      fetchSettings();
      setLoading(false);
    }
    
    // Load sidebar state
    const collapsed = localStorage.getItem('sidebar-collapsed');
    if (collapsed === 'true') setIsCollapsed(true);
  }, [router]);

  const fetchSettings = async () => {
    try {
      const response = await api.get('/settings/');
      setSettings(response.data);
    } catch (error) {
      console.error("Failed to load settings:", error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    router.push('/login');
  };

  const toggleSidebar = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    localStorage.setItem('sidebar-collapsed', String(newState));
  };

  if (loading) return null;

  const brandName = settings?.brand_name || "Hatron";

  return (
    <div className="page-container animate-fade-in">
      {/* Sidebar Navigation */}
      <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`} style={{ 
        backgroundColor: 'var(--bg-secondary)', 
        borderRight: '1px solid var(--border-color)',
        boxShadow: '4px 0 24px rgba(0,0,0,0.02)'
      }}>
        {/* Brand & Toggle Header */}
        <div 
          style={{ 
            padding: '0.5rem 0 2rem 0', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: isCollapsed ? 'center' : 'space-between',
            gap: '0.75rem',
            position: 'relative'
          }}
        >
          <div 
            onClick={() => router.push('/dashboard')}
            style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer', overflow: 'hidden' }}
          >
            <img 
              src="/images/logo.png" 
              alt="Logo" 
              style={{ minWidth: '32px', width: '32px', height: '32px', borderRadius: '8px', objectFit: 'contain' }} 
            />
            {!isCollapsed && (
              <span style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
                {brandName}
              </span>
            )}
          </div>
          
          <button 
            onClick={toggleSidebar}
            style={{
              width: '24px', height: '24px', borderRadius: '6px', backgroundColor: 'var(--bg-tertiary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
              border: '1px solid var(--border-color)', color: 'var(--text-secondary)',
              position: isCollapsed ? 'absolute' : 'relative',
              right: isCollapsed ? '-12px' : '0',
              top: isCollapsed ? '40px' : '0',
              zIndex: 100,
              boxShadow: 'var(--glass-shadow)'
            }}
          >
            {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1, overflowY: 'auto', overflowX: 'hidden' }}>
          {!isCollapsed && (
            <div style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-tertiary)', letterSpacing: '0.05em', marginBottom: '0.5rem', marginTop: '1rem' }}>
              Workspaces
            </div>
          )}
          {MODULES.map((mod) => {
            const active = pathname.startsWith(mod.path);
            return (
              <div 
                key={mod.name}
                onClick={() => router.push(mod.path)}
                title={isCollapsed ? mod.name : ''}
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-md)', cursor: 'pointer',
                  backgroundColor: active ? 'var(--brand-100)' : 'transparent',
                  color: active ? 'var(--brand-500)' : 'var(--text-secondary)',
                  fontWeight: active ? 600 : 500,
                  transition: 'all 0.2s ease',
                  border: active ? '1px solid var(--brand-100)' : '1px solid transparent',
                  justifyContent: isCollapsed ? 'center' : 'flex-start'
                }}
                onMouseEnter={(e) => {
                  if (!active) {
                    e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
                    e.currentTarget.style.color = 'var(--text-primary)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!active) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }
                }}
              >
                <mod.icon size={18} style={{ minWidth: '18px' }} />
                {!isCollapsed && <span style={{ whiteSpace: 'nowrap' }}>{mod.name}</span>}
              </div>
            );
          })}
        </nav>

        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem', marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div 
            onClick={() => router.push('/dashboard/settings')}
            title={isCollapsed ? 'System Config' : ''}
            style={{ 
              display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer', 
              color: pathname === '/dashboard/settings' ? 'var(--brand-500)' : 'var(--text-secondary)',
              backgroundColor: pathname === '/dashboard/settings' ? 'var(--brand-100)' : 'transparent',
              padding: '0.6rem 1rem', borderRadius: 'var(--radius-md)',
              fontWeight: pathname === '/dashboard/settings' ? 600 : 500,
              border: pathname === '/dashboard/settings' ? '1px solid var(--brand-100)' : '1px solid transparent',
              justifyContent: isCollapsed ? 'center' : 'flex-start'
            }}
          >
            <Settings size={18} style={{ minWidth: '18px' }} />
            {!isCollapsed && <span style={{ whiteSpace: 'nowrap' }}>System Config</span>}
          </div>
          <div 
            onClick={handleLogout}
            title={isCollapsed ? 'Sign Out' : ''}
            style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer', color: 'var(--error)', padding: '0.6rem 1rem', borderRadius: 'var(--radius-md)', fontWeight: 500, justifyContent: isCollapsed ? 'center' : 'flex-start' }}
          >
            <LogOut size={18} style={{ minWidth: '18px' }} />
            {!isCollapsed && <span style={{ whiteSpace: 'nowrap' }}>Sign Out</span>}
          </div>
        </div>
      </aside>

      {/* Main App Content View */}
      <main className={`main-content ${isCollapsed ? 'collapsed' : ''}`}>
        <header className="header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', width: '400px', backgroundColor: 'var(--bg-tertiary)', padding: '0.5rem 1rem', borderRadius: '100px', border: '1px solid var(--border-color)' }}>
            <Search size={16} className="text-muted" />
            <input 
              type="text" 
              placeholder="Search across all modules (Orders, Contacts, Inventory...)" 
              style={{ border: 'none', background: 'transparent', outline: 'none', width: '100%', fontSize: '0.9rem', color: 'var(--text-primary)' }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <ThemeToggle />
            <div style={{ cursor: 'pointer', position: 'relative' }} className="text-muted">
              <Bell size={20} />
              <div style={{ position: 'absolute', top: '-2px', right: '-2px', width: '8px', height: '8px', backgroundColor: 'var(--error)', borderRadius: '50%' }}></div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '50%', backgroundColor: 'var(--brand-100)', color: 'var(--brand-700)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                U
              </div>
            </div>
          </div>
        </header>

        <div style={{ flex: 1, backgroundColor: 'var(--bg-primary)' }}>
          {children}
        </div>
      </main>
    </div>
  );
}
