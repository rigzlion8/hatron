"use client";

import { useState, useEffect, useMemo } from 'react';
import { 
  ShoppingCart, 
  ArrowLeft, 
  Plus, 
  Search, 
  FileText, 
  CheckCircle, 
  X,
  Trash2,
  Calendar,
  User,
  Package,
  Loader2
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

// --- Types ---
interface Contact {
  id: string;
  name: string;
  email: string;
}

interface Product {
  id: string;
  name: string;
  price: number;
  sku: string;
}

interface OrderLine {
  product_id: string;
  description: string;
  quantity: number;
  unit_price: number;
  discount: number;
}

interface SalesOrder {
  id: string;
  order_number: string;
  contact_id: string;
  contact: { name: string } | null;
  status: 'draft' | 'confirmed' | 'cancelled';
  expected_date: string;
  amount_total: number;
  created_at: string;
}

const formatKES = (amount: number) => {
  return `KES ${amount.toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('en-KE', { year: 'numeric', month: 'short', day: 'numeric' });
};

export default function SalesPage() {
  const router = useRouter();

  // --- State ---
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [viewOrderId, setViewOrderId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form Data
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  
  const [selectedContact, setSelectedContact] = useState('');
  const [expectedDate, setExpectedDate] = useState('');
  const [orderLines, setOrderLines] = useState<OrderLine[]>([]);

  // --- Initial Fetch ---
  useEffect(() => {
    fetchOrders();
    fetchFormDependencies();
  }, []);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const res = await api.get('/sales/orders?per_page=50');
      // The API returns paginated structure
      setOrders(res.data.items || []);
    } catch (err) {
      console.error("Failed to load orders", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchFormDependencies = async () => {
    try {
      const [contactsRes, productsRes] = await Promise.all([
        api.get('/contacts'),
        api.get('/products?per_page=100')
      ]);
      setContacts(contactsRes.data.items || []);
      setProducts(productsRes.data.items || []);
    } catch (err) {
      console.error("Failed to load dependencies", err);
    }
  };

  // --- Form Handlers ---
  const handleOpenNewOrder = () => {
    setSelectedContact('');
    setExpectedDate(new Date().toISOString().split('T')[0]); // Today
    setOrderLines([]);
    setViewOrderId(null);
    setShowModal(true);
  };

  const addLine = () => {
    if (products.length === 0) return;
    const defaultProduct = products[0];
    setOrderLines([...orderLines, {
      product_id: defaultProduct.id,
      description: defaultProduct.name,
      quantity: 1,
      unit_price: defaultProduct.price,
      discount: 0
    }]);
  };

  const updateLine = (index: number, field: keyof OrderLine, value: any) => {
    setOrderLines(prev => prev.map((line, i) => {
      if (i === index) {
        const updated = { ...line, [field]: value };
        // Auto-update description/price if product changed
        if (field === 'product_id') {
          const product = products.find(p => p.id === value);
          if (product) {
            updated.description = product.name;
            updated.unit_price = product.price;
          }
        }
        return updated;
      }
      return line;
    }));
  };

  const removeLine = (index: number) => {
    setOrderLines(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmitOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedContact) return alert("Select a customer");
    if (orderLines.length === 0) return alert("Add at least one product");

    setIsSubmitting(true);
    try {
      const payload = {
        contact_id: selectedContact,
        expected_date: expectedDate,
        lines: orderLines.map(line => ({
          product_id: line.product_id,
          description: line.description,
          quantity: Number(line.quantity),
          unit_price: Number(line.unit_price),
          discount: Number(line.discount)
        }))
      };

      await api.post('/sales/orders', payload);
      setShowModal(false);
      fetchOrders();
    } catch (err) {
      alert("Failed to create order");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmOrder = async (orderId: string) => {
    if (!confirm("Confirm this order? This will prepare it for invoicing and delivery.")) return;
    try {
      await api.post(`/sales/orders/${orderId}/confirm`);
      fetchOrders(); // Refresh status
    } catch (err) {
      alert("Failed to confirm order");
    }
  };

  // --- Calculations ---
  const lineSubtotals = orderLines.map(line => (line.quantity * line.unit_price) * (1 - line.discount/100));
  const subtotal = lineSubtotals.reduce((a, b) => a + b, 0);
  const tax = subtotal * 0.16; // Assuming 16% VAT
  const grandTotal = subtotal + tax;

  const filteredOrders = useMemo(() => {
    return orders.filter(o => 
      o.order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (o.contact?.name && o.contact.name.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  }, [orders, searchQuery]);

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
              backgroundColor: 'rgba(14, 165, 233, 0.1)', color: '#0ea5e9',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <ShoppingCart size={18} />
            </div>
            <h1 className="heading-2" style={{ margin: 0, fontSize: '1.25rem' }}>Sales & Quotations</h1>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: '250px' }}>
            <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
            <input 
              type="text" 
              className="input" 
              placeholder="Search orders..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ paddingLeft: '2.25rem', width: '100%', borderRadius: '2rem' }}
            />
          </div>
          <button className="btn btn-primary" onClick={handleOpenNewOrder} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <Plus size={18} />
            New Quotation
          </button>
        </div>
      </div>

      {/* Main Content: List */}
      <div style={{ flexGrow: 1, padding: '1.5rem', overflowY: 'auto', backgroundColor: 'var(--bg-secondary)' }}>
        <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Order Number</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Date Created</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Customer</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Expected Date</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Total</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'center' }}>Status</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>
                    <Loader2 size={24} className="animate-spin" style={{ margin: '0 auto' }} />
                  </td>
                </tr>
              ) : filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>
                    No sales orders found
                  </td>
                </tr>
              ) : (
                filteredOrders.map(order => (
                  <tr key={order.id} style={{ borderBottom: '1px solid var(--border-color)', transition: 'background-color 0.2s' }}>
                    <td style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>{order.order_number}</td>
                    <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{formatDate(order.created_at)}</td>
                    <td style={{ padding: '1rem 1.5rem', fontWeight: 500 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div style={{ width: '24px', height: '24px', borderRadius: '50%', backgroundColor: 'var(--bg-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <User size={12} />
                        </div>
                        {order.contact?.name || 'Unknown Contact'}
                      </div>
                    </td>
                    <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{formatDate(order.expected_date)}</td>
                    <td style={{ padding: '1rem 1.5rem', textAlign: 'right', fontWeight: 600 }}>{formatKES(order.amount_total)}</td>
                    <td style={{ padding: '1rem 1.5rem', textAlign: 'center' }}>
                      <span style={{ 
                        padding: '0.25rem 0.75rem', 
                        borderRadius: '1rem', 
                        fontSize: '0.75rem', 
                        fontWeight: 600,
                        backgroundColor: order.status === 'draft' ? 'rgba(245, 158, 11, 0.1)' : 
                                        order.status === 'confirmed' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        color: order.status === 'draft' ? '#d97706' : 
                               order.status === 'confirmed' ? '#059669' : '#dc2626'
                      }}>
                        {order.status.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '1rem 1.5rem', textAlign: 'right' }}>
                      {order.status === 'draft' && (
                        <button 
                          className="btn btn-primary"
                          onClick={() => handleConfirmOrder(order.id)}
                          style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem', float: 'right' }}
                        >
                          <CheckCircle size={14} />
                          Confirm
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* --- New Order Modal --- */}
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
            maxWidth: '1000px', 
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            padding: 0,
            overflow: 'hidden'
          }}>
            {/* Modal Header */}
            <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--bg-secondary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <FileText size={20} color="var(--accent-primary)" />
                <h2 style={{ fontWeight: 600, fontSize: '1.25rem' }}>New Quotation</h2>
              </div>
              <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)' }}>
                <X size={24} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ flexGrow: 1, overflowY: 'auto', padding: '1.5rem' }}>
              <form id="orderForm" onSubmit={handleSubmitOrder}>
                {/* Header Fields */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Customer</label>
                    <select 
                      className="input" 
                      style={{ width: '100%' }}
                      value={selectedContact}
                      onChange={(e) => setSelectedContact(e.target.value)}
                      required
                    >
                      <option value="">Select Customer...</option>
                      {contacts.map(c => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Expected Date</label>
                    <input 
                      type="date" 
                      className="input" 
                      style={{ width: '100%' }}
                      value={expectedDate}
                      onChange={(e) => setExpectedDate(e.target.value)}
                      required
                    />
                  </div>
                </div>

                {/* Order Lines */}
                <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>Order Lines</h3>
                
                {orderLines.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '2rem', border: '2px dashed var(--border-color)', borderRadius: '0.5rem', color: 'var(--text-tertiary)', marginBottom: '1rem' }}>
                    <Package size={32} style={{ margin: '0 auto 0.5rem', opacity: 0.5 }} />
                    <p>No products added yet.</p>
                  </div>
                ) : (
                  <table style={{ width: '100%', marginBottom: '1rem', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-color)' }}>
                        <th style={{ textAlign: 'left', padding: '0.5rem' }}>Product</th>
                        <th style={{ textAlign: 'left', padding: '0.5rem', width: '30%' }}>Description</th>
                        <th style={{ textAlign: 'right', padding: '0.5rem', width: '10%' }}>Qty</th>
                        <th style={{ textAlign: 'right', padding: '0.5rem', width: '15%' }}>Unit Price</th>
                        <th style={{ textAlign: 'right', padding: '0.5rem', width: '15%' }}>Subtotal</th>
                        <th style={{ width: '50px' }}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {orderLines.map((line, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                          <td style={{ padding: '0.5rem' }}>
                            <select 
                              className="input" 
                              style={{ width: '100%', padding: '0.4rem 0.5rem' }}
                              value={line.product_id}
                              onChange={(e) => updateLine(idx, 'product_id', e.target.value)}
                            >
                              {products.map(p => (
                                <option key={p.id} value={p.id}>{p.name}</option>
                              ))}
                            </select>
                          </td>
                          <td style={{ padding: '0.5rem' }}>
                            <input 
                              type="text" 
                              className="input" 
                              style={{ width: '100%', padding: '0.4rem 0.5rem' }}
                              value={line.description}
                              onChange={(e) => updateLine(idx, 'description', e.target.value)}
                            />
                          </td>
                          <td style={{ padding: '0.5rem' }}>
                            <input 
                              type="number" 
                              min="1"
                              className="input" 
                              style={{ width: '100%', padding: '0.4rem 0.5rem', textAlign: 'right' }}
                              value={line.quantity}
                              onChange={(e) => updateLine(idx, 'quantity', Number(e.target.value))}
                            />
                          </td>
                          <td style={{ padding: '0.5rem' }}>
                            <input 
                              type="number" 
                              step="0.01"
                              className="input" 
                              style={{ width: '100%', padding: '0.4rem 0.5rem', textAlign: 'right' }}
                              value={line.unit_price}
                              onChange={(e) => updateLine(idx, 'unit_price', Number(e.target.value))}
                            />
                          </td>
                          <td style={{ padding: '0.5rem', textAlign: 'right', fontWeight: 600 }}>
                            {formatKES(line.quantity * line.unit_price)}
                          </td>
                          <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                            <button type="button" onClick={() => removeLine(idx)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}>
                              <Trash2 size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={addLine}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}
                >
                  <Plus size={16} /> Add Product
                </button>

                {/* Subtotals */}
                <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
                  <div style={{ width: '300px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                      <span>Untaxed Amount:</span>
                      <span>{formatKES(subtotal)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', color: 'var(--text-secondary)' }}>
                      <span>Estimated Tax (16%):</span>
                      <span>{formatKES(tax)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '1rem', borderTop: '2px solid var(--border-color)', fontWeight: 700, fontSize: '1.25rem' }}>
                      <span>Total:</span>
                      <span>{formatKES(grandTotal)}</span>
                    </div>
                  </div>
                </div>
              </form>
            </div>

            {/* Modal Footer */}
            <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button 
                type="submit" 
                form="orderForm" 
                className="btn btn-primary"
                disabled={isSubmitting}
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                Save Quotation
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
