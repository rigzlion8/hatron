"use client";

import { useState, useEffect, useMemo } from 'react';
import { 
  ShoppingCart, 
  ArrowLeft, 
  Search, 
  Plus, 
  CheckCircle,
  FileText,
  Trash2,
  Calendar,
  User,
  Package,
  Loader2,
  X
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

// --- Types ---
interface Contact {
  id: string;
  name: string;
  email: string;
  is_vendor: boolean;
}

interface Product {
  id: string;
  name: string;
  cost: number;
}

interface PurchaseOrderLine {
  id?: string;
  product_id: string;
  description: string;
  quantity: number;
  unit_price: number;
  price_subtotal: number;
}

interface PurchaseOrder {
  id: string;
  order_number: string;
  vendor_id: string;
  status: string;
  order_date: string;
  amount_total: number;
}

const formatKES = (amount: number) => {
  return `KES ${amount.toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

export default function PurchasePage() {
  const router = useRouter();

  // --- State ---
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [vendors, setVendors] = useState<Contact[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [selectedVendor, setSelectedVendor] = useState('');
  const [newLines, setNewLines] = useState<Partial<PurchaseOrderLine>[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // View Order Modal State
  const [viewingOrder, setViewingOrder] = useState<any>(null);

  // --- Initial Fetch ---
  useEffect(() => {
    fetchCoreData();
  }, []);

  const fetchCoreData = async () => {
    try {
      setLoading(true);
      const [orderRes, contactRes, productRes] = await Promise.all([
        api.get('/purchase/orders?per_page=50'),
        api.get('/contacts'),
        api.get('/products?per_page=100')
      ]);
      setOrders(orderRes.data.items || []);
      
      const allContacts: Contact[] = contactRes.data.items || [];
      // Filter for vendors
      setVendors(allContacts.filter(c => c.is_vendor) || []);
      setProducts(productRes.data.items || []);
    } catch (err) {
      console.error("Failed to load purchase page data", err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreate = () => {
    setSelectedVendor('');
    setNewLines([]);
    setShowModal(true);
  };

  const addLine = () => {
    if (products.length === 0) return alert("No products available.");
    const defaultProduct = products[0];
    setNewLines([...newLines, {
      product_id: defaultProduct.id,
      description: defaultProduct.name,
      quantity: 1,
      unit_price: defaultProduct.cost,
      price_subtotal: defaultProduct.cost
    }]);
  };

  const updateLine = (idx: number, field: string, value: any) => {
    const updated = [...newLines];
    if (field === 'product_id') {
      const prod = products.find(p => p.id === value);
      if (prod) {
        updated[idx].product_id = prod.id;
        updated[idx].description = prod.name;
        updated[idx].unit_price = prod.cost;
        updated[idx].price_subtotal = updated[idx].quantity! * prod.cost;
      }
    } else if (field === 'quantity') {
      updated[idx].quantity = Number(value);
      updated[idx].price_subtotal = updated[idx].quantity! * updated[idx].unit_price!;
    } else if (field === 'unit_price') {
      updated[idx].unit_price = Number(value);
      updated[idx].price_subtotal = updated[idx].quantity! * updated[idx].unit_price!;
    }
    setNewLines(updated);
  };

  const removeLine = (idx: number) => {
    setNewLines(newLines.filter((_, i) => i !== idx));
  };

  const calculateTotal = () => {
    const subtotal = newLines.reduce((acc, line) => acc + (line.price_subtotal || 0), 0);
    return subtotal;
  };

  const handleSubmit = async () => {
    if (!selectedVendor) return alert("Please select a vendor.");
    if (newLines.length === 0) return alert("Please add at least one product.");
    
    setIsSubmitting(true);
    try {
      await api.post('/purchase/orders', {
        vendor_id: selectedVendor,
        lines: newLines
      });
      setShowModal(false);
      fetchCoreData();
    } catch (err) {
      console.error("Submit failed", err);
      alert("Failed to create purchase order.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenOrder = async (orderId: string) => {
    try {
      const res = await api.get(`/purchase/orders/${orderId}`);
      setViewingOrder(res.data);
    } catch (err) {
      console.error("Failed to load order", err);
    }
  };

  const handleConfirmOrder = async (orderId: string) => {
    try {
      await api.post(`/purchase/orders/${orderId}/confirm`);
      alert("Purchase Order Confirmed! An incoming stock receipt has been generated in Inventory.");
      setViewingOrder(null);
      fetchCoreData();
    } catch (err) {
      console.error("Failed to confirm order", err);
      alert("Failed to confirm order.");
    }
  };

  // --- Computed ---
  const filteredOrders = useMemo(() => {
    return orders.filter(o => 
      o.order_number.toLowerCase().includes(searchQuery.toLowerCase())
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
              backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#ef4444',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <ShoppingCart size={18} />
            </div>
            <h1 className="heading-2" style={{ margin: 0, fontSize: '1.25rem' }}>Purchasing & Procurement</h1>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: '250px' }}>
            <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
            <input 
              type="text" 
              className="input" 
              placeholder="Search RFQs..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ paddingLeft: '2.25rem', width: '100%', borderRadius: '2rem' }}
            />
          </div>
          <button className="btn btn-primary" onClick={handleOpenCreate} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <Plus size={18} />
            New RFQ
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flexGrow: 1, padding: '1.5rem', overflowY: 'auto', backgroundColor: 'var(--bg-secondary)' }}>
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ backgroundColor: 'var(--bg-tertiary)', borderBottom: '1px solid var(--border-color)' }}>
              <tr>
                <th style={{ textAlign: 'left', padding: '1rem 1.5rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Order #</th>
                <th style={{ textAlign: 'left', padding: '1rem 1.5rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Date</th>
                <th style={{ textAlign: 'left', padding: '1rem 1.5rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Vendor</th>
                <th style={{ textAlign: 'center', padding: '1rem 1.5rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Status</th>
                <th style={{ textAlign: 'right', padding: '1rem 1.5rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Total</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>
                     <Loader2 size={24} className="animate-spin" style={{ margin: '0 auto' }} />
                  </td>
                </tr>
              ) : filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>No Purchase Orders found.</td>
                </tr>
              ) : (
                filteredOrders.map(order => {
                  const vendor = vendors.find(c => c.id === order.vendor_id);
                  return (
                    <tr 
                      key={order.id} 
                      onClick={() => handleOpenOrder(order.id)}
                      style={{ borderBottom: '1px solid var(--border-color)', cursor: 'pointer', transition: 'background-color 0.2s' }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <td style={{ padding: '1rem 1.5rem', fontWeight: 500 }}>{order.order_number}</td>
                      <td style={{ padding: '1rem 1.5rem' }}>{new Date(order.order_date).toLocaleDateString()}</td>
                      <td style={{ padding: '1rem 1.5rem' }}>{vendor ? vendor.name : 'Unknown'}</td>
                      <td style={{ padding: '1rem 1.5rem', textAlign: 'center' }}>
                        <span style={{ 
                          padding: '0.25rem 0.75rem', 
                          borderRadius: '1rem', 
                          fontSize: '0.8rem', 
                          fontWeight: 600,
                          backgroundColor: order.status === 'confirmed' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                          color: order.status === 'confirmed' ? '#059669' : '#d97706'
                        }}>
                          {order.status.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ padding: '1rem 1.5rem', textAlign: 'right', fontWeight: 600 }}>
                        {formatKES(order.amount_total)}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* --- Create RFQ Modal --- */}
      {showModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(4px)'
        }}>
          <div className="card animate-fade-in" style={{ width: '90%', maxWidth: '800px', maxHeight: '90vh', display: 'flex', flexDirection: 'column', padding: 0 }}>
            
            <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontWeight: 600, fontSize: '1.25rem' }}>New Request for Quotation</h2>
              <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)' }}>
                <X size={24} />
              </button>
            </div>

            <div style={{ padding: '1.5rem', flexGrow: 1, overflowY: 'auto' }}>
              <div style={{ marginBottom: '2rem' }}>
                <label className="label" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <User size={16} /> Select Vendor
                </label>
                <select className="input" value={selectedVendor} onChange={e => setSelectedVendor(e.target.value)} style={{ width: '100%' }}>
                  <option value="">-- Choose Vendor --</option>
                  {vendors.map(v => (
                    <option key={v.id} value={v.id}>{v.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <label className="label" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: 0 }}>
                    <Package size={16} /> Ordered Products
                  </label>
                  <button type="button" onClick={addLine} className="btn text-brand" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', padding: '0.25rem 0.5rem' }}>
                    <Plus size={16} /> Add Line
                  </button>
                </div>

                {newLines.length === 0 ? (
                  <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px dashed var(--border-color)' }}>
                    <p style={{ color: 'var(--text-tertiary)' }}>No products attached to this order.</p>
                  </div>
                ) : (
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                        <th style={{ textAlign: 'left', paddingBottom: '0.5rem', width: '40%' }}>Product</th>
                        <th style={{ textAlign: 'right', paddingBottom: '0.5rem', width: '20%' }}>Quantity</th>
                        <th style={{ textAlign: 'right', paddingBottom: '0.5rem', width: '20%' }}>Unit Cost</th>
                        <th style={{ textAlign: 'right', paddingBottom: '0.5rem', width: '15%' }}>Subtotal</th>
                        <th style={{ width: '5%' }}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {newLines.map((line, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                          <td style={{ padding: '0.75rem 0' }}>
                            <select className="input" value={line.product_id} onChange={e => updateLine(idx, 'product_id', e.target.value)} style={{ width: '100%' }}>
                              {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                            </select>
                          </td>
                          <td style={{ padding: '0.75rem 0 0.75rem 1rem' }}>
                            <input type="number" min="0" step="0.1" className="input" value={line.quantity} onChange={e => updateLine(idx, 'quantity', e.target.value)} style={{ width: '100%', textAlign: 'right' }} />
                          </td>
                          <td style={{ padding: '0.75rem 0 0.75rem 1rem' }}>
                            <input type="number" min="0" step="0.01" className="input" value={line.unit_price} onChange={e => updateLine(idx, 'unit_price', e.target.value)} style={{ width: '100%', textAlign: 'right' }} />
                          </td>
                          <td style={{ padding: '0.75rem 0 0.75rem 1rem', textAlign: 'right', fontWeight: 600 }}>
                            {formatKES(line.price_subtotal || 0)}
                          </td>
                          <td style={{ padding: '0.75rem 0 0.75rem 1rem', textAlign: 'right' }}>
                            <button type="button" onClick={() => removeLine(idx)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}>
                              <Trash2 size={18} />
                            </button>
                          </td>
                        </tr>
                      ))}
                      <tr>
                        <td colSpan={3} style={{ textAlign: 'right', padding: '1rem', fontWeight: 600 }}>Untaxed Amount:</td>
                        <td style={{ textAlign: 'right', padding: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{formatKES(calculateTotal())}</td>
                        <td></td>
                      </tr>
                    </tbody>
                  </table>
                )}
              </div>
            </div>

            <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSubmit} disabled={isSubmitting || !selectedVendor || newLines.length === 0}>
                {isSubmitting ? 'Processing...' : 'Save Draft RFQ'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --- View Order Modal --- */}
      {viewingOrder && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(4px)'
        }}>
          <div className="card animate-fade-in" style={{ width: '90%', maxWidth: '800px', maxHeight: '90vh', display: 'flex', flexDirection: 'column', padding: 0 }}>
            
            {/* Header */}
            <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--bg-secondary)' }}>
              <div>
                <h2 style={{ fontWeight: 700, fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  {viewingOrder.order_number}
                  <span style={{ 
                    padding: '0.25rem 0.75rem', borderRadius: '1rem', fontSize: '0.8rem', fontWeight: 600,
                    backgroundColor: viewingOrder.status === 'confirmed' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                    color: viewingOrder.status === 'confirmed' ? '#059669' : '#d97706'
                  }}>
                    {viewingOrder.status.toUpperCase()}
                  </span>
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
                  Ordered on {new Date(viewingOrder.order_date).toLocaleDateString()}
                </p>
              </div>
              <button onClick={() => setViewingOrder(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)' }}>
                <X size={24} />
              </button>
            </div>

            {/* Sub-Header Actions */}
            <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', gap: '1rem' }}>
              {viewingOrder.status === 'draft' && (
                <button 
                  onClick={() => handleConfirmOrder(viewingOrder.id)}
                  className="btn btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  <CheckCircle size={18} /> Confirm Order
                </button>
              )}
            </div>

            {/* Body */}
            <div style={{ padding: '1.5rem', flexGrow: 1, overflowY: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Description</th>
                    <th style={{ textAlign: 'right', padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Qty</th>
                    <th style={{ textAlign: 'right', padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Unit Price</th>
                    <th style={{ textAlign: 'right', padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Taxes</th>
                    <th style={{ textAlign: 'right', padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {viewingOrder.lines?.map((line: any) => (
                    <tr key={line.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '1rem', fontWeight: 500 }}>{line.description}</td>
                      <td style={{ padding: '1rem', textAlign: 'right' }}>{line.quantity}</td>
                      <td style={{ padding: '1rem', textAlign: 'right' }}>{formatKES(line.unit_price)}</td>
                      <td style={{ padding: '1rem', textAlign: 'right', color: 'var(--text-tertiary)' }}>0%</td>
                      <td style={{ padding: '1rem', textAlign: 'right', fontWeight: 600 }}>{formatKES(line.price_subtotal)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2rem' }}>
                <div style={{ width: '300px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', color: 'var(--text-secondary)' }}>
                    <span>Untaxed Amount:</span>
                    <span style={{ fontWeight: 600 }}>{formatKES(viewingOrder.amount_untaxed || 0)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', color: 'var(--text-secondary)' }}>
                    <span>Taxes:</span>
                    <span style={{ fontWeight: 600 }}>{formatKES(viewingOrder.amount_tax || 0)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem 0', borderTop: '1px solid var(--border-color)', marginTop: '0.5rem', fontSize: '1.25rem' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Total:</span>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{formatKES(viewingOrder.amount_total || 0)}</span>
                  </div>
                </div>
              </div>
            </div>
            
          </div>
        </div>
      )}

    </div>
  );
}
