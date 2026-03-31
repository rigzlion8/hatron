"use client";

import { useState, useEffect, useMemo } from 'react';
import { 
  Wallet, 
  ArrowLeft, 
  Search, 
  FileText, 
  CheckCircle, 
  X,
  CreditCard,
  Building,
  Banknote,
  AlertCircle
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

// --- Types ---
interface Contact {
  id: string;
  name: string;
}

interface InvoiceLine {
  id: string;
  description: string;
  quantity: number;
  unit_price: number;
  price_subtotal: number;
}

interface Payment {
  id: string;
  amount: number;
  payment_date: string;
  payment_method: string;
}

interface Invoice {
  id: string;
  invoice_number: string;
  contact_id: string;
  status: 'draft' | 'open' | 'paid' | 'cancelled';
  type: string;
  invoice_date: string;
  due_date: string;
  amount_untaxed: number;
  amount_tax: number;
  amount_total: number;
  amount_residual: number;
  contact?: Contact | null;
  lines?: InvoiceLine[];
  payments?: Payment[];
}

const formatKES = (amount: number) => {
  return `KES ${amount.toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('en-KE', { year: 'numeric', month: 'short', day: 'numeric' });
};

export default function InvoicingPage() {
  const router = useRouter();

  // --- State ---
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Modals
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [invoiceLoading, setInvoiceLoading] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  // Payment Form
  const [paymentAmount, setPaymentAmount] = useState<string>('');
  const [paymentMethod, setPaymentMethod] = useState<string>('bank');
  const [paymentSubmitting, setPaymentSubmitting] = useState(false);

  // --- Initial Fetch ---
  useEffect(() => {
    fetchInvoices();
  }, []);

  const fetchInvoices = async () => {
    try {
      setLoading(true);
      const res = await api.get('/invoicing/invoices?per_page=50');
      setInvoices(res.data.items || []);
    } catch (err) {
      console.error("Failed to load invoices", err);
    } finally {
      setLoading(false);
    }
  };

  // --- Handlers ---
  const handleViewInvoice = async (id: string) => {
    setInvoiceLoading(true);
    setSelectedInvoice(null);
    try {
      const res = await api.get(`/invoicing/invoices/${id}`);
      setSelectedInvoice(res.data);
    } catch (err) {
      alert("Failed to load invoice details");
    } finally {
      setInvoiceLoading(false);
    }
  };

  const handleConfirmInvoice = async () => {
    if (!selectedInvoice) return;
    try {
      await api.patch(`/invoicing/invoices/${selectedInvoice.id}/state`, { status: 'open' });
      // Refresh
      handleViewInvoice(selectedInvoice.id);
      fetchInvoices();
    } catch (err) {
      alert("Failed to confirm invoice");
    }
  };

  const handleOpenPayment = () => {
    if (!selectedInvoice) return;
    setPaymentAmount(selectedInvoice.amount_residual.toString());
    setPaymentMethod('bank');
    setShowPaymentModal(true);
  };

  const handleSubmitPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInvoice) return;
    
    setPaymentSubmitting(true);
    try {
      await api.post(`/invoicing/invoices/${selectedInvoice.id}/payments`, {
        amount: Number(paymentAmount),
        payment_method: paymentMethod
      });
      setShowPaymentModal(false);
      handleViewInvoice(selectedInvoice.id);
      fetchInvoices();
    } catch (err: any) {
      alert(err.response?.data?.error || "Failed to register payment");
    } finally {
      setPaymentSubmitting(false);
    }
  };

  const filteredInvoices = useMemo(() => {
    return invoices.filter(i => 
      i.invoice_number.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [invoices, searchQuery]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)' }}>
      {/* Top Bar */}
      <div style={{ 
        padding: '1.5rem', 
        borderBottom: '1px solid var(--border-color)',
        backgroundColor: 'var(--bg-primary)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button onClick={() => router.push('/dashboard')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>
            <ArrowLeft size={20} />
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ 
              width: '32px', height: '32px', borderRadius: '0.5rem', 
              backgroundColor: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Wallet size={18} />
            </div>
            <h1 className="heading-2" style={{ margin: 0, fontSize: '1.25rem' }}>Invoicing & Payments</h1>
          </div>
        </div>

        <div style={{ position: 'relative', width: '250px' }}>
          <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
          <input 
            type="text" 
            className="input" 
            placeholder="Search invoices..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: '2.25rem', width: '100%', borderRadius: '2rem' }}
          />
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flexGrow: 1, padding: '1.5rem', overflowY: 'auto', backgroundColor: 'var(--bg-secondary)' }}>
        <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Number</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Date</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Customer</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Total</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Amount Due</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'center' }}>Status</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>Loading invoices...</td>
                </tr>
              ) : filteredInvoices.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>No invoices found. Generate them from Sales Orders!</td>
                </tr>
              ) : (
                filteredInvoices.map(inv => (
                  <tr key={inv.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <FileText size={16} color="var(--accent-primary)" />
                        {inv.invoice_number}
                      </div>
                    </td>
                    <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{formatDate(inv.invoice_date)}</td>
                    <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)' }}>
                       {inv.contact ? inv.contact.name : 'Unknown Customer'}
                    </td>
                    <td style={{ padding: '1rem 1.5rem', textAlign: 'right', fontWeight: 600 }}>{formatKES(inv.amount_total)}</td>
                    <td style={{ padding: '1rem 1.5rem', textAlign: 'right', fontWeight: 600, color: inv.amount_residual > 0 ? '#ef4444' : '#10b981' }}>
                      {formatKES(inv.amount_residual)}
                    </td>
                    <td style={{ padding: '1rem 1.5rem', textAlign: 'center' }}>
                      <span style={{ 
                        padding: '0.25rem 0.75rem', 
                        borderRadius: '1rem', 
                        fontSize: '0.75rem', 
                        fontWeight: 600,
                        backgroundColor: inv.status === 'draft' ? 'rgba(107, 114, 128, 0.1)' : 
                                        inv.status === 'paid' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(14, 165, 233, 0.1)',
                        color: inv.status === 'draft' ? '#6b7280' : 
                               inv.status === 'paid' ? '#059669' : '#0284c7'
                      }}>
                        {inv.status.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '1rem 1.5rem', textAlign: 'right' }}>
                      <button 
                        className="btn btn-secondary"
                        onClick={() => handleViewInvoice(inv.id)}
                        style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem' }}
                      >
                        Open
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* --- Invoice Modal --- */}
      {(invoiceLoading || selectedInvoice) && (
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
            maxWidth: '1000px', 
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            padding: 0,
            overflow: 'hidden'
          }}>
            {/* Modal Header */}
            <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--bg-secondary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <FileText size={20} color="var(--accent-primary)" />
                <h2 style={{ fontWeight: 600, fontSize: '1.25rem' }}>
                  {selectedInvoice ? `Invoice: ${selectedInvoice.invoice_number}` : 'Loading...'}
                </h2>
                {selectedInvoice && (
                  <span style={{ 
                    padding: '0.2rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', fontWeight: 600,
                    backgroundColor: selectedInvoice.status === 'paid' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                    color: selectedInvoice.status === 'paid' ? '#059669' : '#d97706'
                  }}>
                    {selectedInvoice.status.toUpperCase()}
                  </span>
                )}
              </div>
              <button onClick={() => setSelectedInvoice(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)' }}>
                <X size={24} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ flexGrow: 1, overflowY: 'auto', padding: '1.5rem', backgroundColor: '#fdfdfd' }}>
              {invoiceLoading ? (
                <div style={{ textAlign: 'center', padding: '3rem' }}>Loading Invoice Details...</div>
              ) : selectedInvoice ? (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem' }}>
                    <div>
                      <h1 style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>INVOICE</h1>
                      <p style={{ color: 'var(--text-secondary)' }}>#{selectedInvoice.invoice_number}</p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Billed To</p>
                      <p style={{ fontWeight: 600, fontSize: '1.1rem' }}>{selectedInvoice.contact?.name || 'Unknown'}</p>
                      <div style={{ marginTop: '1rem' }}>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Date: <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{formatDate(selectedInvoice.invoice_date)}</span></p>
                      </div>
                    </div>
                  </div>

                  <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '2rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: 'var(--bg-secondary)', borderBottom: '2px solid var(--border-color)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        <th style={{ textAlign: 'left', padding: '0.75rem' }}>Description</th>
                        <th style={{ textAlign: 'right', padding: '0.75rem' }}>Qty</th>
                        <th style={{ textAlign: 'right', padding: '0.75rem' }}>Unit Price</th>
                        <th style={{ textAlign: 'right', padding: '0.75rem' }}>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedInvoice.lines?.map((line) => (
                        <tr key={line.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                          <td style={{ padding: '0.75rem', fontWeight: 500 }}>{line.description}</td>
                          <td style={{ padding: '0.75rem', textAlign: 'right' }}>{Number(line.quantity)}</td>
                          <td style={{ padding: '0.75rem', textAlign: 'right' }}>{formatKES(line.unit_price)}</td>
                          <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 600 }}>{formatKES(line.price_subtotal)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '3rem' }}>
                    <div style={{ width: '300px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', color: 'var(--text-secondary)' }}>
                        <span>Subtotal:</span>
                        <span>{formatKES(selectedInvoice.amount_untaxed)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', color: 'var(--text-secondary)' }}>
                        <span>Tax:</span>
                        <span>{formatKES(selectedInvoice.amount_tax)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem 0', borderTop: '2px solid var(--border-color)', fontWeight: 700, fontSize: '1.25rem' }}>
                        <span>Grand Total:</span>
                        <span>{formatKES(selectedInvoice.amount_total)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', fontWeight: 700, color: selectedInvoice.amount_residual > 0 ? '#ef4444' : '#10b981' }}>
                        <span>Amount Due:</span>
                        <span>{formatKES(selectedInvoice.amount_residual)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Payment History */}
                  {selectedInvoice.payments && selectedInvoice.payments.length > 0 && (
                    <div style={{ marginTop: '2rem' }}>
                      <h4 style={{ fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Payment History</h4>
                      <div style={{ border: '1px solid var(--border-color)', borderRadius: '0.5rem', overflow: 'hidden' }}>
                        {selectedInvoice.payments.map(p => (
                          <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)', fontSize: '0.85rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
                              <CheckCircle size={14} color="#10b981" />
                              {formatDate(p.payment_date)} • {p.payment_method.toUpperCase()}
                            </div>
                            <div style={{ fontWeight: 600 }}>{formatKES(p.amount)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : null}
            </div>

            {/* Modal Footer */}
            <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                 {selectedInvoice && selectedInvoice.status === 'draft' && (
                  <button 
                    className="btn btn-secondary"
                    onClick={handleConfirmInvoice}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                  >
                    <CheckCircle size={16} />
                    Confirm Invoice
                  </button>
                 )}
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setSelectedInvoice(null)}>Close</button>
                {selectedInvoice && selectedInvoice.status === 'open' && selectedInvoice.amount_residual > 0 && (
                  <button 
                    className="btn btn-primary"
                    onClick={handleOpenPayment}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'linear-gradient(135deg, #10b981, #059669)' }}
                  >
                    <Banknote size={16} />
                    Register Payment
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --- Register Payment Modal --- */}
      {showPaymentModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)',
          zIndex: 1050,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <div className="card animate-fade-in" style={{ width: '90%', maxWidth: '400px', padding: '2rem' }}>
            <h3 style={{ fontWeight: 600, fontSize: '1.25rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Banknote color="var(--accent-primary)" size={20} />
              Register Payment
            </h3>

            <form onSubmit={handleSubmitPayment}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Payment Amount ({formatKES(Number(selectedInvoice?.amount_residual))})</label>
                <input 
                  type="number" 
                  step="0.01"
                  max={selectedInvoice?.amount_residual}
                  required
                  className="input" 
                  style={{ width: '100%' }}
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                />
              </div>

              <div style={{ marginBottom: '2rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Payment Method</label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    type="button"
                    onClick={() => setPaymentMethod('bank')}
                    style={{
                      flex: 1, padding: '0.75rem', borderRadius: '0.5rem',
                      border: paymentMethod === 'bank' ? '2px solid var(--accent-primary)' : '2px solid var(--border-color)',
                      backgroundColor: paymentMethod === 'bank' ? 'rgba(99, 102, 241, 0.1)' : 'var(--bg-secondary)',
                      color: paymentMethod === 'bank' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem'
                    }}
                  >
                    <Building size={18} />
                    <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>Bank</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setPaymentMethod('cash')}
                    style={{
                      flex: 1, padding: '0.75rem', borderRadius: '0.5rem',
                      border: paymentMethod === 'cash' ? '2px solid var(--accent-primary)' : '2px solid var(--border-color)',
                      backgroundColor: paymentMethod === 'cash' ? 'rgba(99, 102, 241, 0.1)' : 'var(--bg-secondary)',
                      color: paymentMethod === 'cash' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem'
                    }}
                  >
                    <Banknote size={18} />
                    <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>Cash</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setPaymentMethod('card')}
                    style={{
                      flex: 1, padding: '0.75rem', borderRadius: '0.5rem',
                      border: paymentMethod === 'card' ? '2px solid var(--accent-primary)' : '2px solid var(--border-color)',
                      backgroundColor: paymentMethod === 'card' ? 'rgba(99, 102, 241, 0.1)' : 'var(--bg-secondary)',
                      color: paymentMethod === 'card' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem'
                    }}
                  >
                    <CreditCard size={18} />
                    <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>Card</span>
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowPaymentModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={paymentSubmitting}>
                  {paymentSubmitting ? 'Processing...' : 'Create Payment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
