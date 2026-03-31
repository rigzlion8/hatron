"use client";

import { useState, useEffect } from 'react';
import { 
  Settings, 
  Palette, 
  Globe, 
  CreditCard, 
  Save, 
  Image as ImageIcon,
  Type,
  Layout
} from 'lucide-react';
import api from '@/lib/api';

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('branding');
  const [settings, setSettings] = useState({
    brand_name: 'Hatron',
    footer_text: '',
    logo_url: '',
    favicon_url: '',
    payment_settings: {}
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await api.get('/settings/');
      setSettings(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Failed to load settings:", error);
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/settings/', settings);
      alert("Settings updated successfully!");
    } catch (error) {
      console.error("Save failed:", error);
      alert("Failed to save settings.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <div className="animate-pulse text-muted">Loading System Configuration...</div>
    </div>
  );

  return (
    <div className="animate-fade-in" style={{ padding: '2rem', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            System Configuration
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Manage your ERP SaaS identity, branding, and global preferences.
          </p>
        </div>
        <button 
          onClick={handleSave}
          disabled={saving}
          className="btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          {saving ? 'Saving...' : <><Save size={18} /> Save Changes</>}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '250px 1fr', gap: '3rem' }}>
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {[
            { id: 'branding', label: 'Branding', icon: Palette },
            { id: 'general', label: 'General UI', icon: Globe },
            { id: 'payments', label: 'Payment Channels', icon: CreditCard },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-md)',
                border: 'none',
                backgroundColor: activeTab === tab.id ? 'var(--brand-50)' : 'transparent',
                color: activeTab === tab.id ? 'var(--brand-600)' : 'var(--text-secondary)',
                fontWeight: activeTab === tab.id ? 600 : 500,
                textAlign: 'left',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              <tab.icon size={18} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Form Content */}
        <div className="card" style={{ padding: '2rem' }}>
          {activeTab === 'branding' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem', fontWeight: 600 }}>
                <ImageIcon size={20} className="text-brand" /> Visual Identity
              </h3>
              
              <div style={{ display: 'flex', gap: '2rem', alignItems: 'start' }}>
                <div style={{ flex: 1 }}>
                  <label className="label">Brand Name</label>
                  <input 
                    type="text" 
                    className="input" 
                    value={settings.brand_name}
                    onChange={(e) => setSettings({...settings, brand_name: e.target.value})}
                    placeholder="e.g. Hatron"
                  />
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '0.5rem' }}>
                    This name appears in the browser tab, sidebar, and login page.
                  </p>
                </div>
                
                <div style={{ 
                  width: '120px', 
                  height: '120px', 
                  backgroundColor: 'var(--bg-tertiary)', 
                  borderRadius: 'var(--radius-lg)', 
                  border: '2px dashed var(--border-color)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexDirection: 'column',
                  gap: '0.5rem'
                }}>
                   <img 
                    src="/images/logo.png" 
                    alt="Logo Preview" 
                    style={{ width: '60px', height: '60px', objectFit: 'contain' }} 
                  />
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>Current Logo</span>
                </div>
              </div>

              <div style={{ marginTop: '1rem' }}>
                <label className="label">Footer Text</label>
                <textarea 
                  className="input" 
                  rows={3}
                  value={settings.footer_text || ''}
                  onChange={(e) => setSettings({...settings, footer_text: e.target.value})}
                  placeholder="e.g. © 2026 Hatron Solutions Inc. All rights reserved."
                />
              </div>
            </div>
          )}

          {activeTab === 'general' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem', fontWeight: 600 }}>
                <Layout size={20} className="text-brand" /> Layout Settings
              </h3>
              <p className="text-muted">General UI preferences and header customizations will appear here.</p>
              <div className="alert alert-info">
                UI customization engine is currently in beta.
              </div>
            </div>
          )}

          {activeTab === 'payments' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem', fontWeight: 600 }}>
                <CreditCard size={20} className="text-brand" /> Payment Channels
              </h3>
              <p className="text-muted">Configure your connected payment gateways for invoicing and POS.</p>
              
              <div style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontWeight: 600 }}>Stripe Connect</div>
                  <div style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', backgroundColor: 'var(--success-bg)', color: 'var(--success)', borderRadius: '100px', fontWeight: 600 }}>DISCONNECTED</div>
                </div>
              </div>

               <div style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '1rem', opacity: 0.6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontWeight: 600 }}>PayPal Business</div>
                  <div style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-tertiary)', borderRadius: '100px', fontWeight: 600 }}>COMING SOON</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
