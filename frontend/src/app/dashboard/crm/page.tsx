"use client";

import { useState, useEffect } from 'react';
import { 
  Users, Plus, Search, Star, DollarSign, Calendar, Building, Mail, Phone, ExternalLink, X, Briefcase, ArrowRight, CheckCircle
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

// --- Types ---
interface CrmStage {
  id: string;
  name: string;
  sequence: number;
  probability: number;
  fold: boolean;
}

interface CrmPipeline {
  id: string;
  name: string;
  stages: CrmStage[];
}

interface CrmLead {
  id: string;
  name: string;
  contact_id?: string;
  stage_id?: string;
  expected_revenue: number;
  probability: number;
  priority: number;
  status: string;
  expected_close?: string;
}

interface Contact {
  id: string;
  name: string;
  email: string;
  phone?: string;
  type: string;
}

const formatKES = (amount: number) => {
  return `KES ${amount.toLocaleString('en-KE', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
};

export default function CRMPage() {
  const router = useRouter();

  // --- State ---
  const [pipeline, setPipeline] = useState<CrmPipeline | null>(null);
  const [leads, setLeads] = useState<CrmLead[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Modals
  const [showLeadModal, setShowLeadModal] = useState(false);
  const [activeLead, setActiveLead] = useState<Partial<CrmLead> | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchCRMData();
  }, []);

  const fetchCRMData = async () => {
    try {
      setLoading(true);
      const [pipeRes, leadsRes, contactsRes] = await Promise.all([
        api.get('/crm/pipelines'),
        api.get('/crm/leads?per_page=100'),
        api.get('/contacts')
      ]);
      
      if (pipeRes.data && pipeRes.data.length > 0) {
        setPipeline(pipeRes.data[0]);
      }
      setLeads(leadsRes.data.items || []);
      setContacts(contactsRes.data || []);
    } catch (err) {
      console.error("Failed to load CRM data", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLead = () => {
    const firstStageId = pipeline?.stages[0]?.id;
    setActiveLead({
      name: '',
      expected_revenue: 0,
      probability: pipeline?.stages[0]?.probability || 0,
      priority: 0,
      stage_id: firstStageId,
      status: 'open'
    });
    setShowLeadModal(true);
  };

  const handleEditLead = (lead: CrmLead) => {
    setActiveLead(lead);
    setShowLeadModal(true);
  };

  const handleSaveLead = async () => {
    if (!activeLead?.name) return alert("Lead Title is required");
    
    setIsSubmitting(true);
    try {
      if (activeLead.id) {
        // Update
        await api.patch(`/crm/leads/${activeLead.id}`, {
          name: activeLead.name,
          expected_revenue: activeLead.expected_revenue,
          probability: activeLead.probability,
          priority: activeLead.priority,
          contact_id: activeLead.contact_id || null,
        });
        
        // Update Stage if changed
        const originalLead = leads.find(l => l.id === activeLead.id);
        if (originalLead && originalLead.stage_id !== activeLead.stage_id) {
          await api.patch(`/crm/leads/${activeLead.id}/move`, {
            stage_id: activeLead.stage_id
          });
        }
      } else {
        // Create
        await api.post('/crm/leads', {
          ...activeLead,
          contact_id: activeLead.contact_id || null,
        });
      }
      
      setShowLeadModal(false);
      fetchCRMData();
    } catch (err) {
      console.error("Save lead failed", err);
      alert("Failed to save lead.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleMoveStageForward = async (e: React.MouseEvent, lead: CrmLead) => {
    e.stopPropagation(); // prevent opening edit modal
    if (!pipeline) return;
    
    const currentIndex = pipeline.stages.findIndex(s => s.id === lead.stage_id);
    if (currentIndex >= 0 && currentIndex < pipeline.stages.length - 1) {
      const nextStage = pipeline.stages[currentIndex + 1];
      try {
        await api.patch(`/crm/leads/${lead.id}/move`, { stage_id: nextStage.id });
        fetchCRMData();
      } catch (err) {
        console.error("Move failed", err);
      }
    }
  };

  const handleMarkWon = async (e: React.MouseEvent, lead: CrmLead) => {
    e.stopPropagation();
    try {
       await api.patch(`/crm/leads/${lead.id}/move`, { status: 'won' });
       fetchCRMData();
    } catch (err) {
       console.error("Mark won failed", err);
    }
  };

  // --- Render Helpers ---
  const renderPriorityStars = (priority: number) => {
    const stars = [];
    for (let i = 0; i < 3; i++) {
        stars.push(
          <Star 
            key={i} 
            size={14} 
            color={i < priority ? "#f59e0b" : "#e5e7eb"} 
            fill={i < priority ? "#f59e0b" : "transparent"} 
          />
        );
    }
    return <div style={{ display: 'flex', gap: '2px' }}>{stars}</div>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-muted">Loading CRM Pipeline...</div>
      </div>
    );
  }

  if (!pipeline) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="card text-center" style={{ maxWidth: '400px' }}>
          <Briefcase size={48} className="text-muted mx-auto mb-4" />
          <h2 className="heading-2">No Pipeline Configured</h2>
          <p className="text-muted mb-4">You need to configure a default CRM Pipeline to track leads. Please load the Demo Data via POS.</p>
        </div>
      </div>
    );
  }

  // Filter Leads
  const filteredLeads = leads.filter(l => 
    l.name.toLowerCase().includes(searchQuery.toLowerCase()) && l.status === 'open'
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)' }}>
      {/* Top Bar */}
      <div style={{ 
        padding: '1.5rem', 
        borderBottom: '1px solid var(--border-color)',
        backgroundColor: 'var(--bg-primary)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ 
              width: '32px', height: '32px', borderRadius: '0.5rem', 
              backgroundColor: 'rgba(56, 189, 248, 0.1)', color: '#0ea5e9',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Briefcase size={18} />
            </div>
            <h1 className="heading-2" style={{ margin: 0, fontSize: '1.25rem' }}>Sales Pipeline</h1>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: '250px' }}>
            <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
            <input 
              type="text" 
              className="input" 
              placeholder="Search Leads..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ paddingLeft: '2.25rem', width: '100%', borderRadius: '2rem' }}
            />
          </div>
          <button className="btn btn-primary" onClick={handleCreateLead} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <Plus size={18} />
            New Lead
          </button>
        </div>
      </div>

      {/* Main Kanban Board */}
      <div style={{ 
        flexGrow: 1, 
        padding: '1.5rem', 
        backgroundColor: 'var(--bg-secondary)', 
        overflowX: 'auto',
        display: 'flex',
        gap: '1.5rem'
      }}>
        {pipeline.stages.map((stage, sIdx) => {
          const stageLeads = filteredLeads.filter(l => l.stage_id === stage.id);
          const expectedRevenue = stageLeads.reduce((acc, l) => acc + Number(l.expected_revenue), 0);
          
          return (
            <div key={stage.id} style={{ 
              minWidth: '320px', 
              width: '320px', 
              display: 'flex', 
              flexDirection: 'column',
              backgroundColor: 'var(--bg-primary)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-color)',
              height: 'fit-content',
              maxHeight: '100%'
            }}>
              {/* Stage Header */}
              <div style={{ 
                padding: '1rem', 
                borderBottom: '2px solid var(--brand-500)', 
                display: 'flex', 
                flexDirection: 'column', 
                gap: '0.25rem' 
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontWeight: 600, fontSize: '1rem', margin: 0 }}>{stage.name}</h3>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', fontWeight: 600, backgroundColor: 'var(--bg-tertiary)', padding: '0.1rem 0.5rem', borderRadius: '1rem' }}>
                    {stageLeads.length}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  <span>{formatKES(expectedRevenue)}</span>
                  <span style={{ color: 'var(--brand-600)', fontWeight: 500 }}>{stage.probability}% Win</span>
                </div>
              </div>

              {/* Stage Body (Cards) */}
              <div style={{ 
                padding: '1rem', 
                display: 'flex', 
                flexDirection: 'column', 
                gap: '1rem',
                overflowY: 'auto',
                flexGrow: 1
              }}>
                {stageLeads.map(lead => {
                  const contact = contacts.find(c => c.id === lead.contact_id);
                  const isLastStage = sIdx === pipeline.stages.length - 1;
                  
                  return (
                    <div 
                      key={lead.id} 
                      onClick={() => handleEditLead(lead)}
                      style={{ 
                        backgroundColor: 'var(--bg-primary)', 
                        border: '1px solid var(--border-color)', 
                        borderRadius: 'var(--radius-md)', 
                        padding: '1rem',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
                        cursor: 'pointer',
                        transition: 'transform 0.1s, box-shadow 0.1s',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-2px)';
                        e.currentTarget.style.boxShadow = '0 6px 12px rgba(0,0,0,0.05)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.02)';
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                        <h4 style={{ fontWeight: 600, fontSize: '0.95rem', margin: 0, color: 'var(--text-primary)' }}>{lead.name}</h4>
                        {renderPriorityStars(lead.priority)}
                      </div>
                      
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Building size={14} />
                        {contact ? contact.name : 'Unknown Contact'}
                      </div>
                      
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px dashed var(--border-color)', paddingTop: '0.75rem', marginTop: '0.5rem' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                          {formatKES(lead.expected_revenue)}
                        </div>
                        
                        {!isLastStage ? (
                          <button 
                            onClick={(e) => handleMoveStageForward(e, lead)}
                            style={{ 
                              background: 'var(--bg-tertiary)', 
                              border: 'none', 
                              borderRadius: '50%', 
                              width: '24px', 
                              height: '24px', 
                              display: 'flex', 
                              alignItems: 'center', 
                              justifyContent: 'center',
                              cursor: 'pointer',
                              color: 'var(--brand-600)'
                            }}
                            title="Move to next stage"
                          >
                            <ArrowRight size={14} />
                          </button>
                        ) : (
                          <button 
                            onClick={(e) => handleMarkWon(e, lead)}
                            style={{ 
                              background: 'rgba(16, 185, 129, 0.1)', 
                              border: 'none', 
                              borderRadius: '50%', 
                              padding: '0.25rem 0.5rem',
                              display: 'flex', 
                              alignItems: 'center', 
                              gap: '0.25rem',
                              cursor: 'pointer',
                              color: '#059669',
                              fontSize: '0.75rem',
                              fontWeight: 600
                            }}
                            title="Mark as Won"
                          >
                            <CheckCircle size={14} /> Won
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )
        })}
      </div>

      {/* --- Create/Edit Lead Modal --- */}
      {showLeadModal && activeLead && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(4px)'
        }}>
          <div className="card animate-fade-in" style={{ width: '90%', maxWidth: '600px', display: 'flex', flexDirection: 'column', padding: 0 }}>
            
            <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--brand-50)' }}>
              <h2 style={{ fontWeight: 600, fontSize: '1.25rem', color: 'var(--brand-700)' }}>
                {activeLead.id ? 'Edit Opportunity' : 'New Lead / Opportunity'}
              </h2>
              <button onClick={() => setShowLeadModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)' }}>
                <X size={24} />
              </button>
            </div>

            <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxHeight: '70vh', overflowY: 'auto' }}>
              <div>
                <label className="label">Opportunity Title *</label>
                <input 
                  type="text" 
                  className="input" 
                  value={activeLead.name || ''}
                  onChange={(e) => setActiveLead({...activeLead, name: e.target.value})}
                  placeholder="e.g. Acme Q3 Upgrade"
                  style={{ width: '100%', fontSize: '1.1rem', fontWeight: 600, padding: '0.75rem' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                <div>
                  <label className="label">Expected Revenue (KES)</label>
                  <input 
                    type="number" 
                    className="input" 
                    value={activeLead.expected_revenue || 0}
                    onChange={(e) => setActiveLead({...activeLead, expected_revenue: Number(e.target.value)})}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label className="label">Probability (%)</label>
                  <input 
                    type="number" 
                    className="input" 
                    value={activeLead.probability || 0}
                    onChange={(e) => setActiveLead({...activeLead, probability: Number(e.target.value)})}
                    style={{ width: '100%' }}
                    max="100"
                    min="0"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                <div>
                  <label className="label">Customer / Contact</label>
                  <select 
                    className="input" 
                    value={activeLead.contact_id || ''}
                    onChange={(e) => setActiveLead({...activeLead, contact_id: e.target.value})}
                    style={{ width: '100%' }}
                  >
                    <option value="">-- Unassigned --</option>
                    {contacts.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Priority Level (0-3)</label>
                  <select 
                    className="input" 
                    value={activeLead.priority || 0}
                    onChange={(e) => setActiveLead({...activeLead, priority: Number(e.target.value)})}
                    style={{ width: '100%' }}
                  >
                    <option value="0">Low</option>
                    <option value="1">Medium</option>
                    <option value="2">High</option>
                    <option value="3">Critical</option>
                  </select>
                </div>
              </div>

               <div>
                  <label className="label">Pipeline Stage</label>
                  <select 
                    className="input" 
                    value={activeLead.stage_id || ''}
                    onChange={(e) => setActiveLead({...activeLead, stage_id: e.target.value})}
                    style={{ width: '100%' }}
                  >
                    {pipeline.stages.map(s => (
                      <option key={s.id} value={s.id}>{s.name} ({s.probability}%)</option>
                    ))}
                  </select>
                </div>

            </div>

            <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button className="btn btn-secondary" onClick={() => setShowLeadModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSaveLead} disabled={isSubmitting}>
                {isSubmitting ? 'Saving...' : 'Save Lead'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
