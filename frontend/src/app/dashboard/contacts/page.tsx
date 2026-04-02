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

export default function ContactsPage() {
  const router = useRouter();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchContacts();
  }, []);

  const fetchContacts = async () => {
    try {
      setLoading(true);
      const res = await api.get('/contacts?per_page=100');
      setContacts(res.data.items || []);
    } catch (err) {
      console.error('Failed to load contacts', err);
    } finally {
      setLoading(false);
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
          <button className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }} onClick={() => alert('Create contact is not implemented yet, but API supports /contacts POST')}>
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
    </div>
  );
}
