"use client";

import { useState, useEffect, useMemo } from 'react';
import { 
  Package, 
  ArrowLeft, 
  Search, 
  Plus, 
  Box, 
  X,
  CheckCircle,
  Tag,
  Hash,
  Activity,
  Trash2
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

// --- Types ---
interface ProductCategory {
  id: string;
  name: string;
}

interface Product {
  id: string;
  name: string;
  sku: string;
  type: string;
  category_id: string | null;
  price: number;
  cost: number;
  description_sales: string | null;
  attributes: Record<string, string> | null;
  is_active: boolean;
  category?: ProductCategory;
  image_url?: string | null;
}

interface StockQuant {
  id: string;
  product_id: string;
  quantity: number;
}

const formatKES = (amount: number) => {
  return `KES ${amount.toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

export default function ProductsPage() {
  const router = useRouter();

  // --- State ---
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [quants, setQuants] = useState<StockQuant[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Partial<Product> | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [dynamicAttributes, setDynamicAttributes] = useState<{key: string, value: string}[]>([]);

  // --- Initial Fetch ---
  useEffect(() => {
    fetchCoreData();
  }, []);

  const fetchCoreData = async () => {
    try {
      setLoading(true);
      const [prodRes, catRes, quantRes] = await Promise.all([
        api.get('/products?per_page=100'),
        api.get('/products/categories'),
        api.get('/inventory/quants') // Used to compute On Hand
      ]);
      setProducts(prodRes.data.items || []);
      setCategories(catRes.data || []);
      setQuants(quantRes.data || []);
    } catch (err) {
      console.error("Failed to load products page data", err);
    } finally {
      setLoading(false);
    }
  };

  // --- Handlers ---
  const handleOpenCreate = () => {
    setEditingProduct({
      name: '',
      sku: '',
      price: 0,
      cost: 0,
      type: 'storable',
      category_id: categories.length > 0 ? categories[0].id : null,
      is_active: true
    });
    setDynamicAttributes([]);
    setShowModal(true);
  };

  const handleOpenEdit = (prod: Product) => {
    setEditingProduct(prod);
    const attrs = prod.attributes || {};
    setDynamicAttributes(Object.entries(attrs).map(([key, value]) => ({ key, value })));
    setShowModal(true);
  };

  const handleAddAttribute = () => {
    setDynamicAttributes([...dynamicAttributes, { key: '', value: '' }]);
  };

  const handleUpdateAttribute = (index: number, field: 'key' | 'value', val: string) => {
    setDynamicAttributes(prev => prev.map((attr, i) => i === index ? { ...attr, [field]: val } : attr));
  };

  const handleRemoveAttribute = (index: number) => {
    setDynamicAttributes(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProduct) return;
    
    setIsSubmitting(true);
    
    // Flatten dynamic attributes array into a generic object
    const finalAttributes: Record<string, string> = {};
    dynamicAttributes.forEach(attr => {
      if (attr.key.trim() !== '') {
        finalAttributes[attr.key.trim()] = attr.value.trim();
      }
    });

    const payload = {
      ...editingProduct,
      attributes: Object.keys(finalAttributes).length > 0 ? finalAttributes : null
    };

    try {
      if (editingProduct.id) {
        await api.patch(`/products/${editingProduct.id}`, payload);
      } else {
        await api.post('/products', payload);
      }
      setShowModal(false);
      fetchCoreData();
    } catch (err) {
      alert("Failed to save product details");
    } finally {
      setIsSubmitting(false);
    }
  };

  // --- Computed ---
  // Returns total quantity across all configured locations (vendor, customer, internal).
  // Ideally, this UI should filter just for internal locations, but for simplicity we'll sum.
  const getQuantityOnHand = (productId: string) => {
    return quants
      .filter(q => q.product_id === productId)
      .reduce((sum, q) => sum + Number(q.quantity), 0);
  };

  const filteredProducts = useMemo(() => {
    return products.filter(p => 
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
      (p.sku && p.sku.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  }, [products, searchQuery]);

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
              backgroundColor: 'rgba(99, 102, 241, 0.1)', color: '#6366f1',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Package size={18} />
            </div>
            <h1 className="heading-2" style={{ margin: 0, fontSize: '1.25rem' }}>Product Catalog</h1>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: '250px' }}>
            <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
            <input 
              type="text" 
              className="input" 
              placeholder="Search products..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ paddingLeft: '2.25rem', width: '100%', borderRadius: '2rem' }}
            />
          </div>
          <button className="btn btn-primary" onClick={handleOpenCreate} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <Plus size={18} />
            New Product
          </button>
        </div>
      </div>

      {/* Main Content: Grid */}
      <div style={{ flexGrow: 1, padding: '1.5rem', overflowY: 'auto', backgroundColor: 'var(--bg-secondary)' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>Loading products...</div>
        ) : filteredProducts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>No products found.</div>
        ) : (
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', 
            gap: '1.5rem' 
          }}>
            {filteredProducts.map(prod => {
              const qty = getQuantityOnHand(prod.id);
              return (
                <div 
                  key={prod.id} 
                  className="card" 
                  style={{ 
                    padding: '1.5rem', 
                    cursor: 'pointer', 
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    position: 'relative'
                  }}
                  onClick={() => handleOpenEdit(prod)}
                  onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
                  onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                >
                  <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                    <div style={{ 
                      width: '60px', height: '60px', borderRadius: '0.5rem', 
                      backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      overflow: 'hidden'
                    }}>
                      {prod.image_url ? (
                        <img src={prod.image_url} alt={prod.name} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                      ) : (
                        <Box size={24} color="var(--text-tertiary)" />
                      )}
                    </div>
                    <div>
                      <h3 style={{ fontWeight: 600, fontSize: '1.1rem', marginBottom: '0.25rem' }}>{prod.name}</h3>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                        <Hash size={12} /> {prod.sku || 'No SKU'}
                      </div>
                    </div>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '1.5rem' }}>
                    <div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Sales Price</p>
                      <p style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{formatKES(prod.price)}</p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ 
                        padding: '0.3rem 0.6rem', borderRadius: '1rem', fontSize: '0.75rem', fontWeight: 600,
                        backgroundColor: qty > 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        color: qty > 0 ? '#059669' : '#dc2626',
                        display: 'flex', alignItems: 'center', gap: '0.25rem'
                      }}>
                        <Activity size={12} />
                        {qty} On Hand
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* --- Product Modal --- */}
      {showModal && editingProduct && (
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
            maxWidth: '700px', 
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            padding: 0,
            overflow: 'hidden'
          }}>
            {/* Modal Header */}
            <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--bg-secondary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Package size={20} color="var(--accent-primary)" />
                <h2 style={{ fontWeight: 600, fontSize: '1.25rem' }}>
                  {editingProduct.id ? `Edit: ${editingProduct.name}` : 'New Product'}
                </h2>
              </div>
              <button type="button" onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)' }}>
                <X size={24} />
              </button>
            </div>

            {/* Smart Buttons */}
            {editingProduct.id && (
              <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--bg-primary)', display: 'flex', gap: '1rem' }}>
                <button 
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => router.push(`/dashboard/inventory?search=${editingProduct.sku}`)}
                  style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '0.5rem 1rem', width: '120px' }}
                >
                  <span style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-primary)' }}>{getQuantityOnHand(editingProduct.id as string)}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>On Hand</span>
                </button>
              </div>
            )}

            {/* Modal Body */}
            <div style={{ flexGrow: 1, overflowY: 'auto', padding: '1.5rem' }}>
              <form id="productForm" onSubmit={handleSubmit}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}>Product Name</label>
                    <input 
                      type="text" 
                      className="input" 
                      style={{ width: '100%' }}
                      required
                      value={editingProduct.name || ''}
                      onChange={(e) => setEditingProduct({...editingProduct, name: e.target.value})}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}>SKU</label>
                    <input 
                      type="text" 
                      className="input" 
                      style={{ width: '100%' }}
                      value={editingProduct.sku || ''}
                      onChange={(e) => setEditingProduct({...editingProduct, sku: e.target.value})}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}>Sales Price (KES)</label>
                    <input 
                      type="number" 
                      step="0.01"
                      className="input" 
                      style={{ width: '100%' }}
                      required
                      value={editingProduct.price || 0}
                      onChange={(e) => setEditingProduct({...editingProduct, price: Number(e.target.value)})}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}>Cost (KES)</label>
                    <input 
                      type="number" 
                      step="0.01"
                      className="input" 
                      style={{ width: '100%' }}
                      value={editingProduct.cost || 0}
                      onChange={(e) => setEditingProduct({...editingProduct, cost: Number(e.target.value)})}
                    />
                  </div>
                </div>

                <div style={{ marginBottom: '2rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}>Category</label>
                  <select 
                    className="input" 
                    style={{ width: '100%' }}
                    value={editingProduct.category_id || ''}
                    onChange={(e) => setEditingProduct({...editingProduct, category_id: e.target.value})}
                  >
                    <option value="">No Category</option>
                    {categories.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                {/* --- DYNAMIC ATTRIBUTES --- */}
                <div style={{ padding: '1.5rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Tag size={16} color="var(--accent-primary)" />
                    Dynamic Attributes (Sizes, Colors, etc.)
                  </h3>
                  
                  {dynamicAttributes.map((attr, idx) => (
                    <div key={idx} style={{ display: 'flex', gap: '1rem', marginBottom: '0.75rem' }}>
                      <input 
                        type="text" 
                        className="input" 
                        placeholder="e.g. Size"
                        style={{ flex: 1 }}
                        value={attr.key}
                        onChange={(e) => handleUpdateAttribute(idx, 'key', e.target.value)}
                      />
                      <input 
                        type="text" 
                        className="input" 
                        placeholder="e.g. XL"
                        style={{ flex: 1 }}
                        value={attr.value}
                        onChange={(e) => handleUpdateAttribute(idx, 'value', e.target.value)}
                      />
                      <button 
                        type="button" 
                        onClick={() => handleRemoveAttribute(idx)}
                        style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '0.5rem' }}
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  ))}

                  <button 
                    type="button" 
                    className="btn btn-secondary" 
                    onClick={handleAddAttribute}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', padding: '0.4rem 0.8rem', marginTop: '0.5rem' }}
                  >
                    <Plus size={14} /> Add Attribute
                  </button>
                </div>
              </form>
            </div>

            {/* Modal Footer */}
            <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button 
                type="submit" 
                form="productForm" 
                className="btn btn-primary"
                disabled={isSubmitting}
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                {isSubmitting ? 'Saving...' : <CheckCircle size={16} />}
                Save Product
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
