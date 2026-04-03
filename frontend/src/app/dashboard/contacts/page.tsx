"use client";

import { useState, useEffect, useMemo } from 'react';
import { 
  Users,
  ArrowLeft,
  Search,
  Plus,
  Trash2,
  Loader2,
  CheckCircle,
  X
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

interface Contact {
  id: string;
  name: string;
  email: string;
  phone?: string;
  type: string;
  is_customer: boolean;
  is_vendor: boolean;
}

interface ContactFormData {
  name: string;
  email: string;
  phone: string;
  mobile: string;
  type: 'individual' | 'company';
  is_customer: boolean;
  is_vendor: boolean;
  website: string;
  tax_id: string;
  notes: string;
}

const defaultFormData: ContactFormData = {
  name: '',
  email: '',
  phone: '',
  mobile: '',
  type: 'individual',
  is_customer: false,
  is_vendor: false,
  website: '',
  tax_id: '',
  notes: ''
};

export default function ContactsPage() {
  const router = useRouter();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<ContactFormData>(defaultFormData);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchContacts();
  }, []);

  const fetchContacts = async () => {
    try {
      setLoading(true);
      const res = await api.get('/contacts?per_page=100');
      setContacts(res.data.data || []);
    } catch (err) {
      console.error('Failed to load contacts', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreate = () => {
    setFormData(defaultFormData);
    setShowModal(true);
  };

  const handleInputChange = (field: keyof ContactFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      alert('Name is required');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        name: formData.name.trim(),
        email: formData.email.trim() || undefined,
        phone: formData.phone.trim() || undefined,
        mobile: formData.mobile.trim() || undefined,
        type: formData.type,
        is_customer: formData.is_customer,
        is_vendor: formData.is_vendor,
        website: formData.website.trim() || undefined,
        tax_id: formData.tax_id.trim() || undefined,
        notes: formData.notes.trim() || undefined
      };
      
      await api.post('/contacts', payload);
      setShowModal(false);
      await fetchContacts();
    } catch (err) {
      console.error('Failed to create contact', err);
      alert('Failed to create contact');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filtered = useMemo(() => {
    return contacts.filter(c =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.email || '').toLowerCase().includes(search.toLowerCase()) ||
      (c.phone || '').toLowerCase().includes(search.toLowerCase())
    );
  }, [contacts, search]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)' }}>
      <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--bg-primary)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button onClick={() => router.push('/dashboard')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}><ArrowLeft size={20}/></button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '0.5rem', backgroundColor: 'rgba(34, 211, 238, 0.1)', color: '#22d3ee', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Users size={18}/></div>
            <h1 className="heading-2" style={{ margin: 0, fontSize: '1.25rem' }}>Contacts</h1>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ position: 'relative', width: '300px' }}>
            <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search contacts" className="input" style={{ paddingLeft: '2.25rem', width: '100%', borderRadius: '2rem' }} />
          </div>
          <button className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }} onClick={handleOpenCreate}>
            <Plus size={16} /> New Contact
          </button>
        </div>
      </div>

      <div style={{ flex: 1, padding: '1.5rem', overflowY: 'auto', backgroundColor: 'var(--bg-secondary)' }}>
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--bg-tertiary)', borderBottom: '1px solid var(--border-color)' }}>
                <th style={{ padding: '1rem 1.5rem' }}>Name</th>
                <th style={{ padding: '1rem 1.5rem' }}>Email</th>
                <th style={{ padding: '1rem 1.5rem' }}>Phone</th>
                <th style={{ padding: '1rem 1.5rem' }}>Type</th>
                <th style={{ padding: '1rem 1.5rem' }}>Tags</th>
                <th style={{ padding: '1rem 1.5rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem' }}><Loader2 className="animate-spin" /> Loading contacts...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem' }}>No contacts found.</td></tr>
              ) : filtered.map(contact => (
                <tr key={contact.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '1rem 1.5rem' }}>{contact.name}</td>
                  <td style={{ padding: '1rem 1.5rem' }}>{contact.email}</td>
                  <td style={{ padding: '1rem 1.5rem' }}>{contact.phone || '-'}</td>
                  <td style={{ padding: '1rem 1.5rem' }}>{contact.type}</td>
                  <td style={{ padding: '1rem 1.5rem' }}>
                    {contact.is_customer && <span style={{ marginRight: '0.35rem', padding: '0.15rem 0.5rem', background: 'rgba(16, 185, 129, 0.12)', color: '#059669', borderRadius: '999px' }}>Customer</span>}
                    {contact.is_vendor && <span style={{ padding: '0.15rem 0.5rem', background: 'rgba(37, 99, 235, 0.12)', color: '#1d4ed8', borderRadius: '999px' }}>Vendor</span>}
                  </td>
                  <td style={{ padding: '1rem 1.5rem', textAlign: 'right' }}>
                    <button className="btn btn-small" style={{ marginRight: '0.5rem' }} onClick={() => router.push(`/dashboard/contacts/${contact.id}`)}>View</button>
                    <button className="btn btn-ghost" onClick={() => alert('edit stub')}><X size={14} /></button>
                  </td>
                </tr>
              )) }
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Contact Modal */}
      {showModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backdropFilter: 'blur(4px)'
        }}>
          <div className="card animate-fade-in" style={{ 
            width: '90%', 
            maxWidth: '600px', 
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            padding: 0,
            overflow: 'hidden'
          }}>
            {/* Modal Header */}
            <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--bg-secondary)' }}>
              <h2 style={{ fontWeight: 600, fontSize: '1.25rem', margin: 0 }}>New Contact</h2>
              <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <form onSubmit={handleSubmit} style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {/* Name */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Name *</label>
                <input
                  type="text"
                  className="input"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="Contact name"
                  required
                />
              </div>

              {/* Type */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Type</label>
                <select
                  className="input"
                  value={formData.type}
                  onChange={(e) => handleInputChange('type', e.target.value as 'individual' | 'company')}
                >
                  <option value="individual">Individual</option>
                  <option value="company">Company</option>
                </select>
              </div>

              {/* Email */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Email</label>
                <input
                  type="email"
                  className="input"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  placeholder="email@example.com"
                />
              </div>

              {/* Phone & Mobile */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Phone</label>
                  <input
                    type="tel"
                    className="input"
                    value={formData.phone}
                    onChange={(e) => handleInputChange('phone', e.target.value)}
                    placeholder="Phone"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Mobile</label>
                  <input
                    type="tel"
                    className="input"
                    value={formData.mobile}
                    onChange={(e) => handleInputChange('mobile', e.target.value)}
                    placeholder="Mobile"
                  />
                </div>
              </div>

              {/* Website & Tax ID */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Website</label>
                  <input
                    type="text"
                    className="input"
                    value={formData.website}
                    onChange={(e) => handleInputChange('website', e.target.value)}
                    placeholder="https://..."
                  />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Tax ID</label>
                  <input
                    type="text"
                    className="input"
                    value={formData.tax_id}
                    onChange={(e) => handleInputChange('tax_id', e.target.value)}
                    placeholder="Tax ID"
                  />
                </div>
              </div>

              {/* Checkboxes */}
              <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={formData.is_customer}
                    onChange={(e) => handleInputChange('is_customer', e.target.checked)}
                  />
                  Is Customer
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={formData.is_vendor}
                    onChange={(e) => handleInputChange('is_vendor', e.target.checked)}
                  />
                  Is Vendor
                </label>
              </div>

              {/* Notes */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Notes</label>
                <textarea
                  className="input"
                  value={formData.notes}
                  onChange={(e) => handleInputChange('notes', e.target.value)}
                  placeholder="Additional notes..."
                  rows={3}
                />
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => setShowModal(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isSubmitting}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                  {isSubmitting ? 'Creating...' : 'Create Contact'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
