"use client";

import { useState, useEffect, useMemo } from 'react';
import { 
  Building2, 
  ArrowLeft, 
  Package, 
  ArrowRightLeft, 
  CheckCircle, 
  X,
  Search,
  Box,
  Truck
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

// --- Types ---
interface Product {
  id: string;
  name: string;
  sku: string;
}

interface Location {
  id: string;
  name: string;
  type: string;
}

interface StockQuant {
  id: string;
  product_id: string;
  location_id: string;
  quantity: number;
  updated_at: string;
}

interface StockMove {
  id: string;
  name: string;
  product_id: string;
  quantity: number;
  quantity_done: number;
  status: string;
}

interface StockPicking {
  id: string;
  picking_number: string;
  type: 'incoming' | 'outgoing' | 'internal';
  status: string;
  created_at: string;
  location_id: string;
  location_dest_id: string;
  moves?: StockMove[];
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleString('en-KE', { 
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
};

export default function InventoryPage() {
  const router = useRouter();

  // --- State ---
  const [activeTab, setActiveTab] = useState<'stock' | 'operations'>('stock');
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Data State
  const [quants, setQuants] = useState<StockQuant[]>([]);
  const [pickings, setPickings] = useState<StockPicking[]>([]);
  const [products, setProducts] = useState<Record<string, Product>>({});
  const [locations, setLocations] = useState<Record<string, Location>>({});

  // Modal State
  const [selectedPicking, setSelectedPicking] = useState<StockPicking | null>(null);
  const [pickingLoading, setPickingLoading] = useState(false);
  const [validating, setValidating] = useState(false);

  // --- Initial Fetch ---
  useEffect(() => {
    fetchCoreData();
  }, []);

  useEffect(() => {
    if (activeTab === 'stock') {
      fetchQuants();
    } else {
      fetchPickings();
    }
  }, [activeTab]);

  const fetchCoreData = async () => {
    try {
      const [prodRes, locRes] = await Promise.all([
        api.get('/products?per_page=100'),
        api.get('/inventory/locations')
      ]);
      
      const prodMap: Record<string, Product> = {};
      (prodRes.data.items || []).forEach((p: Product) => prodMap[p.id] = p);
      setProducts(prodMap);

      const locMap: Record<string, Location> = {};
      (locRes.data || []).forEach((l: Location) => locMap[l.id] = l);
      setLocations(locMap);
    } catch (err) {
      console.error("Failed to load core inventory data", err);
    }
  };

  const fetchQuants = async () => {
    try {
      setLoading(true);
      const res = await api.get('/inventory/quants');
      setQuants(res.data || []);
    } catch (err) {
      console.error("Failed to load quants", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPickings = async () => {
    try {
      setLoading(true);
      const res = await api.get('/inventory/pickings?per_page=50');
      setPickings(res.data.items || []);
    } catch (err) {
      console.error("Failed to load operations", err);
    } finally {
      setLoading(false);
    }
  };

  // --- Handlers ---
  const handleViewPicking = async (id: string) => {
    setPickingLoading(true);
    setSelectedPicking(null); // Open empty modal first
    try {
      const res = await api.get(`/inventory/pickings/${id}`);
      setSelectedPicking(res.data);
    } catch (err) {
      alert("Failed to load transfer details");
    } finally {
      setPickingLoading(false);
    }
  };

  const updateMoveDoneQuantity = async (moveId: string, quantity: number) => {
    if (!selectedPicking) return;
    
    // Optimistic UI update
    setSelectedPicking({
      ...selectedPicking,
      moves: selectedPicking.moves?.map(m => 
        m.id === moveId ? { ...m, quantity_done: quantity } : m
      )
    });

    try {
      await api.patch(`/inventory/moves/${moveId}`, { quantity_done: quantity });
    } catch (err) {
      alert("Failed to save quantity");
      // Could revert state here
    }
  };

  const handleSetAllDone = () => {
    if (!selectedPicking || !selectedPicking.moves) return;
    selectedPicking.moves.forEach(m => {
      // If it's 0, set it to the demanded quantity
      if (m.quantity_done === 0) {
        updateMoveDoneQuantity(m.id, m.quantity);
      }
    });
  };

  const handleValidatePicking = async () => {
    if (!selectedPicking) return;
    setValidating(true);
    try {
      await api.post(`/inventory/pickings/${selectedPicking.id}/validate`);
      setSelectedPicking(null);
      fetchPickings(); // Refresh list
    } catch (err: any) {
      alert(err.response?.data?.message || err.response?.data?.error || "Failed to validate transfer");
    } finally {
      setValidating(false);
    }
  };

  // --- Computed ---
  const filteredQuants = useMemo(() => {
    return quants.filter(q => {
      const p = products[q.product_id];
      const matchSearch = p?.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          p?.sku?.toLowerCase().includes(searchQuery.toLowerCase());
      // Only show internal locations by default or where quantity > 0
      const isInternal = locations[q.location_id]?.type === 'internal';
      return matchSearch && (isInternal || q.quantity > 0);
    }).sort((a, b) => b.quantity - a.quantity);
  }, [quants, products, locations, searchQuery]);

  const filteredPickings = useMemo(() => {
    return pickings.filter(p => 
      p.picking_number.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [pickings, searchQuery]);

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
              backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#10b981',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Building2 size={18} />
            </div>
            <h1 className="heading-2" style={{ margin: 0, fontSize: '1.25rem' }}>Inventory</h1>
          </div>
        </div>

        <div style={{ position: 'relative', width: '250px' }}>
          <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
          <input 
            type="text" 
            className="input" 
            placeholder="Search..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: '2.25rem', width: '100%', borderRadius: '2rem' }}
          />
        </div>
      </div>

      {/* Tabs */}
      <div style={{ 
        display: 'flex', 
        padding: '0 1.5rem',
        backgroundColor: 'var(--bg-primary)',
        borderBottom: '1px solid var(--border-color)',
        gap: '2rem'
      }}>
        <button 
          onClick={() => setActiveTab('stock')}
          style={{ 
            padding: '1rem 0',
            fontWeight: 600,
            color: activeTab === 'stock' ? 'var(--accent-primary)' : 'var(--text-secondary)',
            borderBottom: activeTab === 'stock' ? '2px solid var(--accent-primary)' : '2px solid transparent',
            background: 'none',
            borderTop: 'none', borderLeft: 'none', borderRight: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <Package size={18} />
          Stock on Hand
        </button>
        <button 
          onClick={() => setActiveTab('operations')}
          style={{ 
            padding: '1rem 0',
            fontWeight: 600,
            color: activeTab === 'operations' ? 'var(--accent-primary)' : 'var(--text-secondary)',
            borderBottom: activeTab === 'operations' ? '2px solid var(--accent-primary)' : '2px solid transparent',
            background: 'none',
            borderTop: 'none', borderLeft: 'none', borderRight: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <ArrowRightLeft size={18} />
          Operations / Transfers
        </button>
      </div>

      {/* Main Content */}
      <div style={{ flexGrow: 1, padding: '1.5rem', overflowY: 'auto', backgroundColor: 'var(--bg-secondary)' }}>
        
        {/* --- STOCK ON HAND VIEW --- */}
        {activeTab === 'stock' && (
          <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Product</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>SKU</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Location</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>On Hand Quantity</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Last Updated</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>Loading stock levels...</td>
                  </tr>
                ) : filteredQuants.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>No internal stock found. Create receipts to stock up!</td>
                  </tr>
                ) : (
                  filteredQuants.map(q => (
                    <tr key={q.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <Box size={16} color="var(--text-secondary)" />
                          {products[q.product_id]?.name || 'Unknown'}
                        </div>
                      </td>
                      <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)' }}>{products[q.product_id]?.sku || '-'}</td>
                      <td style={{ padding: '1rem 1.5rem' }}>
                        <span style={{ 
                          padding: '0.2rem 0.5rem', 
                          borderRadius: '0.25rem', 
                          backgroundColor: 'var(--bg-primary)',
                          border: '1px solid var(--border-color)',
                          fontSize: '0.8rem' 
                        }}>
                          {locations[q.location_id]?.name || 'Unknown Location'}
                        </span>
                      </td>
                      <td style={{ padding: '1rem 1.5rem', textAlign: 'right', fontWeight: 700, color: q.quantity < 0 ? '#ef4444' : 'var(--text-primary)' }}>
                        {Number(q.quantity).toFixed(2)}
                      </td>
                      <td style={{ padding: '1rem 1.5rem', textAlign: 'right', color: 'var(--text-tertiary)', fontSize: '0.85rem' }}>
                        {formatDate(q.updated_at)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* --- OPERATIONS VIEW --- */}
        {activeTab === 'operations' && (
          <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Reference</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>From</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>To</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Created At</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'center' }}>Status</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>Loading operations...</td>
                  </tr>
                ) : filteredPickings.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>No transfers found. Generate orders to create pickings!</td>
                  </tr>
                ) : (
                  filteredPickings.map(p => (
                    <tr key={p.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <Truck size={16} color={p.type === 'incoming' ? '#3b82f6' : p.type === 'outgoing' ? '#f59e0b' : '#6366f1'} />
                          {p.picking_number}
                        </div>
                      </td>
                      <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)' }}>{locations[p.location_id]?.name || 'Unknown'}</td>
                      <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)' }}>{locations[p.location_dest_id]?.name || 'Unknown'}</td>
                      <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{formatDate(p.created_at)}</td>
                      <td style={{ padding: '1rem 1.5rem', textAlign: 'center' }}>
                        <span style={{ 
                          padding: '0.25rem 0.75rem', 
                          borderRadius: '1rem', 
                          fontSize: '0.75rem', 
                          fontWeight: 600,
                          backgroundColor: p.status === 'draft' ? 'rgba(107, 114, 128, 0.1)' : 
                                          p.status === 'done' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                          color: p.status === 'draft' ? '#6b7280' : 
                                 p.status === 'done' ? '#059669' : '#d97706'
                        }}>
                          {p.status.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ padding: '1rem 1.5rem', textAlign: 'right' }}>
                        <button 
                          className="btn btn-secondary"
                          onClick={() => handleViewPicking(p.id)}
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
        )}
      </div>

      {/* --- Picking Modal --- */}
      {(pickingLoading || selectedPicking) && (
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
            maxWidth: '900px', 
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            padding: 0,
            overflow: 'hidden'
          }}>
            {/* Modal Header */}
            <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--bg-secondary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Truck size={20} color="var(--accent-primary)" />
                <h2 style={{ fontWeight: 600, fontSize: '1.25rem' }}>
                  {selectedPicking ? `Transfer: ${selectedPicking.picking_number}` : 'Loading...'}
                </h2>
                {selectedPicking && (
                  <span style={{ 
                     padding: '0.2rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', fontWeight: 600,
                     backgroundColor: selectedPicking.status === 'done' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                     color: selectedPicking.status === 'done' ? '#059669' : '#d97706'
                  }}>
                    {selectedPicking.status.toUpperCase()}
                  </span>
                )}
              </div>
              <button onClick={() => setSelectedPicking(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)' }}>
                <X size={24} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ flexGrow: 1, overflowY: 'auto', padding: '1.5rem' }}>
              {pickingLoading ? (
                <div style={{ textAlign: 'center', padding: '3rem' }}>Loading Transfer Details...</div>
              ) : selectedPicking ? (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
                    <div style={{ padding: '1rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Source Location</p>
                      <p style={{ fontWeight: 600 }}>{locations[selectedPicking.location_id]?.name || selectedPicking.location_id}</p>
                    </div>
                    <div style={{ padding: '1rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Destination Location</p>
                      <p style={{ fontWeight: 600 }}>{locations[selectedPicking.location_dest_id]?.name || selectedPicking.location_dest_id}</p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Operations</h3>
                    {selectedPicking.status !== 'done' && (
                      <button 
                        onClick={handleSetAllDone}
                        style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 500 }}
                      >
                        Set Quantities
                      </button>
                    )}
                  </div>

                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-color)' }}>
                        <th style={{ textAlign: 'left', padding: '0.75rem' }}>Product</th>
                        <th style={{ textAlign: 'center', padding: '0.75rem' }}>Demand</th>
                        <th style={{ textAlign: 'center', padding: '0.75rem' }}>Done</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem' }}>Line Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedPicking.moves?.map((move) => (
                        <tr key={move.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                          <td style={{ padding: '0.75rem', fontWeight: 500 }}>{products[move.product_id]?.name || move.name}</td>
                          <td style={{ padding: '0.75rem', textAlign: 'center' }}>{Number(move.quantity)}</td>
                          <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                            {selectedPicking.status === 'done' ? (
                              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{Number(move.quantity_done)}</span>
                            ) : (
                              <input 
                                type="number"
                                className="input"
                                style={{ width: '80px', textAlign: 'center', padding: '0.25rem' }}
                                value={Number(move.quantity_done)}
                                onChange={(e) => updateMoveDoneQuantity(move.id, Number(e.target.value))}
                                min="0"
                              />
                            )}
                          </td>
                          <td style={{ padding: '0.75rem' }}>
                            <span style={{ color: move.status === 'done' ? '#10b981' : 'var(--text-tertiary)', fontSize: '0.8rem' }}>
                              {move.status.toUpperCase()}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              ) : null}
            </div>

            {/* Modal Footer */}
            <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setSelectedPicking(null)}>Close</button>
              {selectedPicking && selectedPicking.status !== 'done' && (
                <button 
                  className="btn btn-primary"
                  disabled={validating}
                  onClick={handleValidatePicking}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  <CheckCircle size={16} />
                  {validating ? 'Validating...' : 'Validate Transfer'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
