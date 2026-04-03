"use client";

import { useState, useEffect, useMemo } from 'react';
import {
  Monitor,
  ArrowLeft,
  Database,
  ShoppingCart,
  Search,
  CreditCard,
  CheckCircle2,
  AlertCircle,
  Smartphone,
  Banknote,
  Loader2,
  X,
  ScanLine,
  Package
} from 'lucide-react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import ProductCard from '@/components/pos/ProductCard';
import CartItem from '@/components/pos/CartItem';

// --- Types ---
interface Product {
  id: string;
  name: string;
  price: number;
  category_name?: string;
  sku?: string;
  image_url?: string;
}

interface CartItemData extends Product {
  quantity: number;
}

type PaymentMethod = 'cash' | 'mpesa' | 'paystack';

const formatKES = (amount: number) => {
  return `KES ${amount.toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

export default function POSPage() {
  const router = useRouter();
  
  // --- State ---
  const [setupMode, setSetupMode] = useState<'wizard' | 'terminal'>('wizard');
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<CartItemData[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [orderStatus, setOrderStatus] = useState<'idle' | 'processing' | 'success' | 'failed'>('idle');
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // Payment state
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('cash');
  const [mpesaPhone, setMpesaPhone] = useState('');
  const [mpesaStatus, setMpesaStatus] = useState<'idle' | 'pushed' | 'polling' | 'confirmed' | 'failed'>('idle');
  const [mpesaCheckoutId, setMpesaCheckoutId] = useState('');
  const [paymentError, setPaymentError] = useState('');

  // Scanner state
  const [showCameraScanner, setShowCameraScanner] = useState(false);

  // --- Initial Load ---
  useEffect(() => {
    checkRegistration();
  }, []);

  const checkRegistration = async () => {
    try {
      const res = await api.get('/pos/products');
      if (res.data && res.data.length > 0) {
        setProducts(res.data);
        setSetupMode('terminal');
        ensureSession();
      }
    } catch (err) {
      console.error("No products found, staying in wizard mode.");
    }
  };

  const ensureSession = async () => {
    try {
      const res = await api.get('/pos/sessions');
      const openSession = res.data.find((s: any) => s.status === 'open');
      if (openSession) {
        setSessionId(openSession.id);
      } else {
        const startRes = await api.post('/pos/sessions', { name: "Default POS Session" });
        setSessionId(startRes.data.id);
      }
    } catch (err) {
      console.error("Failed to manage session", err);
    }
  };

  // --- Hardware Scanner Hook ---
  useEffect(() => {
    let barcodeString = '';
    let lastKeyTime = Date.now();

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in search or handled by modals
      const target = e.target as HTMLElement;
      if (
        target.tagName.toLowerCase() === 'input' || 
        target.tagName.toLowerCase() === 'textarea' || 
        showPaymentModal || 
        showCameraScanner ||
        setupMode !== 'terminal'
      ) {
        return;
      }

      const currentTime = Date.now();
      
      // Hardware scanners type extremely fast (<50ms per keystroke). 
      // If > 100ms between strokes, likely a human typing, so clear buffer.
      if (currentTime - lastKeyTime > 100) {
        barcodeString = '';
      }
      lastKeyTime = currentTime;

      if (e.key === 'Enter') {
        if (barcodeString.length > 0) {
          const matchedProduct = products.find(p => p.sku?.toLowerCase() === barcodeString.toLowerCase());
          if (matchedProduct) {
            // Found a match via scanner, act like 'addToCart'
            setCart(prev => {
              const existing = prev.find(item => item.id === matchedProduct.id);
              if (existing) {
                return prev.map(item => item.id === matchedProduct.id ? { ...item, quantity: item.quantity + 1 } : item);
              }
              return [...prev, { ...matchedProduct, quantity: 1 }];
            });
          }
          barcodeString = ''; 
        }
      } else if (e.key.length === 1) { 
        barcodeString += e.key;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [products, showPaymentModal, showCameraScanner, setupMode]);

  // --- Camera Scanner Hook ---
  useEffect(() => {
    if (showCameraScanner && setupMode === 'terminal') {
      const scanner = new Html5QrcodeScanner(
        "qr-reader",
        { fps: 10, qrbox: { width: 250, height: 250 }, rememberLastUsedCamera: true },
        false
      );

      scanner.render((decodedText) => {
        const matchedProduct = products.find(p => p.sku?.toLowerCase() === decodedText.toLowerCase());
        if (matchedProduct) {
          // Direct addToCart replication since we can't easily rely on the outside function ref in this callback
          setCart(prev => {
            const existing = prev.find(item => item.id === matchedProduct.id);
            if (existing) {
              return prev.map(item => item.id === matchedProduct.id ? { ...item, quantity: item.quantity + 1 } : item);
            }
            return [...prev, { ...matchedProduct, quantity: 1 }];
          });
        }
        setShowCameraScanner(false);
        scanner.clear();
      }, (error) => {
        // Ignored, occurs constantly on empty frames
      });

      return () => {
        scanner.clear().catch(e => console.error("Scanner clear error", e));
      };
    }
  }, [showCameraScanner, products, setupMode]);

  // --- Handlers ---
  const handleSetup = async (mode: 'demo' | 'clean') => {
    setIsLoading(true);
    try {
      await api.post('/pos/setup', { mode });
      await checkRegistration();
    } catch (err) {
      alert("Failed to setup POS database.");
    } finally {
      setIsLoading(false);
    }
  };

  const addToCart = (product: Product) => {
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item => 
          item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      }
      return [...prev, { ...product, quantity: 1 }];
    });
  };

  const updateQuantity = (id: string, delta: number) => {
    setCart(prev => prev.map(item => {
      if (item.id === id) {
        const newQty = Math.max(1, item.quantity + delta);
        return { ...item, quantity: newQty };
      }
      return item;
    }));
  };

  const removeFromCart = (id: string) => {
    setCart(prev => prev.filter(item => item.id !== id));
  };

  const openPaymentModal = () => {
    if (cart.length === 0 || !sessionId) return;
    setShowPaymentModal(true);
    setPaymentMethod('cash');
    setMpesaStatus('idle');
    setPaymentError('');
    setMpesaPhone('');
  };

  // --- Payment Flows ---
  const handleCashPayment = async () => {
    setOrderStatus('processing');
    setShowPaymentModal(false);
    try {
      const payload = buildOrderPayload('cash');
      await api.post('/pos/orders', payload);
      setOrderStatus('success');
      setCart([]);
      setTimeout(() => setOrderStatus('idle'), 3000);
    } catch (err) {
      setOrderStatus('failed');
      setTimeout(() => setOrderStatus('idle'), 3000);
    }
  };

  const handleMpesaPayment = async () => {
    if (!mpesaPhone) {
      setPaymentError('Please enter a phone number');
      return;
    }
    
    // Format phone number to 254 format
    let phone = mpesaPhone.replace(/\s/g, '');
    if (phone.startsWith('0')) phone = '254' + phone.slice(1);
    if (phone.startsWith('+')) phone = phone.slice(1);
    
    setMpesaStatus('pushed');
    setPaymentError('');

    try {
      const ref = `POS/${Date.now()}`;
      const res = await api.post('/pos/payments/mpesa/initiate', {
        phone_number: phone,
        amount: grandTotal,
        order_reference: ref
      });

      if (res.data.success) {
        setMpesaCheckoutId(res.data.checkout_request_id);
        setMpesaStatus('polling');
        // Poll for status
        pollMpesaStatus(res.data.checkout_request_id, ref);
      } else {
        setMpesaStatus('failed');
        setPaymentError(res.data.error || 'STK Push failed. Try again.');
      }
    } catch (err: any) {
      setMpesaStatus('failed');
      setPaymentError(err?.response?.data?.error || 'M-Pesa request failed.');
    }
  };

  const pollMpesaStatus = async (checkoutId: string, orderRef: string) => {
    let attempts = 0;
    const maxAttempts = 12; // 60 seconds total

    const poll = async () => {
      attempts++;
      try {
        const res = await api.post('/pos/payments/mpesa/status', {
          checkout_request_id: checkoutId
        });

        if (res.data.success) {
          // Payment confirmed — create the order
          setMpesaStatus('confirmed');
          setShowPaymentModal(false);
          setOrderStatus('processing');
          
          const payload = buildOrderPayload('mpesa');
          payload.order_reference = orderRef;
          await api.post('/pos/orders', payload);
          
          setOrderStatus('success');
          setCart([]);
          setTimeout(() => setOrderStatus('idle'), 3000);
          return;
        }

        if (attempts >= maxAttempts) {
          setMpesaStatus('failed');
          setPaymentError('Payment timed out. Check your phone and try again.');
          return;
        }

        // Still pending — poll again in 5 seconds
        setTimeout(poll, 5000);
      } catch {
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setMpesaStatus('failed');
          setPaymentError('Could not verify payment status.');
        }
      }
    };

    setTimeout(poll, 5000); // First poll after 5s
  };

  const handlePaystackPayment = async () => {
    setPaymentError('');
    const ref = `POS-${Date.now()}`;
    
    try {
      const res = await api.post('/pos/payments/paystack/initiate', {
        email: 'pos@hatron.co.ke',
        amount: grandTotal,
        reference: ref,
        callback_url: window.location.href
      });

      if (res.data.success && res.data.authorization_url) {
        // Open Paystack in new window for POS
        const payWindow = window.open(res.data.authorization_url, '_blank', 'width=500,height=600');
        
        // Poll for verification
        setShowPaymentModal(false);
        setOrderStatus('processing');
        pollPaystackStatus(ref);
      } else {
        setPaymentError(res.data.error || 'Paystack initialization failed.');
      }
    } catch (err: any) {
      setPaymentError(err?.response?.data?.error || 'Paystack request failed.');
    }
  };

  const pollPaystackStatus = async (reference: string) => {
    let attempts = 0;
    const maxAttempts = 24; // 2 minutes

    const poll = async () => {
      attempts++;
      try {
        const res = await api.get(`/pos/payments/paystack/verify/${reference}`);
        
        if (res.data.success && res.data.status === 'success') {
          const payload = buildOrderPayload('paystack');
          payload.order_reference = reference;
          await api.post('/pos/orders', payload);
          
          setOrderStatus('success');
          setCart([]);
          setTimeout(() => setOrderStatus('idle'), 3000);
          return;
        }

        if (attempts >= maxAttempts) {
          setOrderStatus('failed');
          setTimeout(() => setOrderStatus('idle'), 3000);
          return;
        }

        setTimeout(poll, 5000);
      } catch {
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setOrderStatus('failed');
          setTimeout(() => setOrderStatus('idle'), 3000);
        }
      }
    };

    setTimeout(poll, 5000);
  };

  const buildOrderPayload = (method: string) => ({
    session_id: sessionId!,
    order_reference: `POS/${Date.now()}`,
    amount_total: grandTotal,
    amount_tax: total * 0.16,
    amount_paid: grandTotal,
    amount_return: 0,
    payment_method: method,
    lines: cart.map(item => ({
      product_id: item.id,
      quantity: item.quantity,
      unit_price: item.price,
      price_subtotal: item.price * item.quantity
    }))
  });

  // --- Computed ---
  const filteredProducts = useMemo(() => {
    return products.filter(p => 
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
      (p.sku && p.sku.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  }, [products, searchQuery]);

  const total = useMemo(() => {
    return cart.reduce((acc, item) => acc + (item.price * item.quantity), 0);
  }, [cart]);

  const tax = total * 0.16; // VAT 16% Kenya
  const grandTotal = total + tax;

  // --- View: Wizard ---
  if (setupMode === 'wizard') {
    return (
      <div style={{ height: 'calc(100vh - 120px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
        <div className="card animate-fade-in" style={{ maxWidth: '500px', width: '100%', padding: '3rem', textAlign: 'center' }}>
          <div style={{ 
            width: '64px', 
            height: '64px', 
            borderRadius: '1rem', 
            backgroundColor: 'rgba(99, 102, 241, 0.1)', 
            color: '#6366f1',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.5rem'
          }}>
            <Monitor size={32} />
          </div>
          
          <h1 className="heading-2" style={{ marginBottom: '1rem' }}>POS Setup</h1>
          <p className="text-secondary" style={{ marginBottom: '2.5rem' }}>
            Choose how you'd like to initialize your Point of Sale terminal.
          </p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <button 
              className="btn btn-primary" 
              onClick={() => handleSetup('demo')}
              disabled={isLoading}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', padding: '1rem' }}
            >
              <Database size={18} />
              {isLoading ? 'Seeding...' : 'Load Demo Data'}
            </button>
            <button 
              className="btn btn-secondary" 
              onClick={() => handleSetup('clean')}
              disabled={isLoading}
              style={{ padding: '1rem' }}
            >
              Start Clean Database
            </button>
            <button 
              className="btn btn-secondary" 
              onClick={() => router.push('/dashboard/products')}
              style={{ padding: '1rem', border: '1px dashed var(--border-color)', color: 'var(--brand-600)', background: 'transparent' }}
            >
              + Add Product Manually
            </button>
          </div>
          
          <div style={{ marginTop: '2rem', fontSize: '0.85rem', color: 'var(--text-tertiary)' }}>
             The demo mode seeds Electronics, Food, and Stationery products.
          </div>
        </div>
      </div>
    );
  }

  // --- View: Terminal ---
  return (
    <div style={{ 
      height: 'calc(100vh - 64px)', 
      display: 'grid', 
      gridTemplateColumns: '1fr 380px',
      gap: '0',
      overflow: 'hidden'
    }}>
      
      {/* --- Left: Product Grid --- */}
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        borderRight: '1px solid var(--border-color)',
        backgroundColor: 'var(--bg-secondary)',
        overflow: 'hidden'
      }}>
        {/* Header/Search */}
        <div style={{ 
          padding: '1.25rem 2rem', 
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: 'var(--bg-primary)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button onClick={() => router.push('/dashboard')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>
              <ArrowLeft size={20} />
            </button>
            <h2 style={{ fontWeight: 600, fontSize: '1.25rem' }}>Terminal View</h2>
            <button 
              onClick={() => setSetupMode('wizard')}
              style={{ 
                marginLeft: '1rem',
                fontSize: '0.75rem', 
                padding: '0.4rem 0.75rem', 
                borderRadius: '0.5rem', 
                border: '1px solid var(--border-color)', 
                background: 'var(--bg-secondary)', 
                cursor: 'pointer',
                color: 'var(--text-secondary)'
              }}
            >
              ⚙️ Setup
            </button>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', width: '380px' }}>
            <div style={{ position: 'relative', flexGrow: 1 }}>
              <div style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }}>
                <Search size={18} />
              </div>
              <input 
                type="text" 
                className="input" 
                placeholder="Search products or SKU..."
                style={{ paddingLeft: '2.5rem', width: '100%', borderRadius: '2rem' }}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            
            <button 
              onClick={() => setShowCameraScanner(true)}
              className="btn btn-secondary"
              title="Camera Scanner"
              style={{
                borderRadius: '2rem',
                width: '42px',
                height: '42px',
                padding: '0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                color: 'var(--text-secondary)'
              }}
            >
              <ScanLine size={18} />
            </button>
          </div>
        </div>

        {/* Grid */}
        <div style={{ 
          flexGrow: 1, 
          overflowY: 'auto', 
          padding: '2rem',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
          gridAutoRows: '280px',
          gap: '1.5rem',
          alignContent: 'start'
        }}>
          {filteredProducts.map(product => (
            <ProductCard key={product.id} product={product} onAdd={addToCart} />
          ))}
          {filteredProducts.length === 0 && (
            <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '6rem 2rem', color: 'var(--text-tertiary)', backgroundColor: 'var(--bg-primary)', borderRadius: '1rem', border: '2px dashed var(--border-color)' }}>
              <Package size={48} style={{ margin: '0 auto 1.5rem', opacity: 0.5 }} />
              <h3 className="heading-3" style={{ marginBottom: '0.5rem' }}>No Products Found</h3>
              <p style={{ marginBottom: '2rem' }}>Add items in the Inventory module or reset your terminal to load demo data.</p>
              <button 
                onClick={() => router.push('/dashboard/products')}
                className="btn btn-primary"
                style={{ padding: '0.75rem 2rem' }}
              >
                Go to Product Management
              </button>
            </div>
          )}
        </div>
      </div>

      {/* --- Right: Cart Sidebar --- */}
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        backgroundColor: 'var(--bg-primary)',
        overflow: 'hidden'
      }}>
        <div style={{ 
          padding: '1.25rem 1.5rem', 
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontWeight: 600 }}>
            <ShoppingCart size={20} color="var(--accent-primary)" />
            Current Order
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>
            #{sessionId?.slice(-6).toUpperCase() || 'OFFLINE'}
          </div>
        </div>

        <div style={{ flexGrow: 1, overflowY: 'auto' }}>
          {cart.length === 0 ? (
            <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-tertiary)', gap: '1rem', padding: '2rem', textAlign: 'center' }}>
              <ShoppingCart size={48} strokeWidth={1} style={{ opacity: 0.3 }} />
              <p>Your cart is empty.<br/>Select items to begin a sale.</p>
            </div>
          ) : (
            cart.map(item => (
              <CartItem 
                key={item.id} 
                item={item} 
                onUpdateQuantity={updateQuantity}
                onRemove={removeFromCart} 
              />
            ))
          )}
        </div>

        {/* Footer: Summary & Checkout */}
        <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
              <span>Subtotal</span>
              <span>{formatKES(total)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
              <span>VAT (16%)</span>
              <span>{formatKES(tax)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, fontSize: '1.25rem', marginTop: '0.5rem', color: 'var(--text-primary)' }}>
              <span>Total</span>
              <span>{formatKES(grandTotal)}</span>
            </div>
          </div>

          <button 
            className="btn btn-primary"
            disabled={cart.length === 0 || orderStatus === 'processing'}
            style={{ 
              width: '100%', 
              padding: '1.1rem', 
              fontSize: '1rem', 
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.75rem'
            }}
            onClick={openPaymentModal}
          >
            {orderStatus === 'processing' ? (
              <>
                <Loader2 size={20} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
                Processing...
              </>
            ) : (
              <>
                <CreditCard size={20} />
                Pay {formatKES(grandTotal)}
              </>
            )}
          </button>
        </div>
      </div>

      {/* --- Payment Method Modal --- */}
      {showPaymentModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backdropFilter: 'blur(8px)'
        }}>
          <div className="card animate-fade-in" style={{ 
            padding: '2rem', 
            maxWidth: '440px', 
            width: '90%',
            position: 'relative' 
          }}>
            <button 
              onClick={() => { setShowPaymentModal(false); setMpesaStatus('idle'); setPaymentError(''); }}
              style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)' }}
            >
              <X size={20} />
            </button>

            <h3 style={{ fontWeight: 700, fontSize: '1.25rem', marginBottom: '0.5rem' }}>Payment Method</h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
              Total: <strong style={{ color: 'var(--text-primary)' }}>{formatKES(grandTotal)}</strong>
            </p>

            {/* Payment Method Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
              {([
                { id: 'cash' as PaymentMethod, label: 'Cash', icon: <Banknote size={18} /> },
                { id: 'mpesa' as PaymentMethod, label: 'M-Pesa', icon: <Smartphone size={18} /> },
                { id: 'paystack' as PaymentMethod, label: 'Card', icon: <CreditCard size={18} /> },
              ]).map(method => (
                <button
                  key={method.id}
                  onClick={() => { setPaymentMethod(method.id); setPaymentError(''); setMpesaStatus('idle'); }}
                  style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '1rem 0.75rem',
                    borderRadius: '0.75rem',
                    border: paymentMethod === method.id 
                      ? '2px solid var(--accent-primary)' 
                      : '2px solid var(--border-color)',
                    backgroundColor: paymentMethod === method.id 
                      ? 'rgba(99, 102, 241, 0.08)' 
                      : 'var(--bg-secondary)',
                    color: paymentMethod === method.id 
                      ? 'var(--accent-primary)' 
                      : 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {method.icon}
                  {method.label}
                </button>
              ))}
            </div>

            {/* Cash Flow */}
            {paymentMethod === 'cash' && (
              <div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
                  Collect <strong>{formatKES(grandTotal)}</strong> in cash from the customer and confirm the payment.
                </p>
                <button 
                  className="btn btn-primary" 
                  onClick={handleCashPayment}
                  style={{ width: '100%', padding: '1rem', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
                >
                  <Banknote size={18} />
                  Confirm Cash Payment
                </button>
              </div>
            )}

            {/* M-Pesa Flow */}
            {paymentMethod === 'mpesa' && (
              <div>
                {mpesaStatus === 'idle' && (
                  <>
                    <div style={{ marginBottom: '1rem' }}>
                      <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                        Customer Phone Number
                      </label>
                      <input
                        type="tel"
                        className="input"
                        placeholder="e.g. 0712 345 678"
                        value={mpesaPhone}
                        onChange={(e) => setMpesaPhone(e.target.value)}
                        style={{ width: '100%' }}
                      />
                    </div>
                    <button 
                      className="btn btn-primary" 
                      onClick={handleMpesaPayment}
                      style={{ 
                        width: '100%', 
                        padding: '1rem', 
                        fontWeight: 600, 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center', 
                        gap: '0.5rem',
                        background: 'linear-gradient(135deg, #4caf50, #2e7d32)'
                      }}
                    >
                      <Smartphone size={18} />
                      Send STK Push
                    </button>
                  </>
                )}

                {(mpesaStatus === 'pushed' || mpesaStatus === 'polling') && (
                  <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
                    <div style={{ 
                      width: '64px', 
                      height: '64px', 
                      borderRadius: '50%', 
                      background: 'linear-gradient(135deg, #4caf50, #2e7d32)',
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      margin: '0 auto 1.25rem',
                      animation: 'pulse 2s infinite'
                    }}>
                      <Smartphone size={28} color="white" />
                    </div>
                    <h4 style={{ fontWeight: 700, marginBottom: '0.5rem' }}>STK Push Sent</h4>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                      A prompt has been sent to <strong>{mpesaPhone}</strong>.<br/>
                      Ask the customer to enter their M-Pesa PIN.
                    </p>
                    <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', color: 'var(--text-tertiary)', fontSize: '0.85rem' }}>
                      <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                      Waiting for confirmation...
                    </div>
                  </div>
                )}

                {mpesaStatus === 'confirmed' && (
                  <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
                    <CheckCircle2 size={48} color="var(--success-color)" style={{ margin: '0 auto 1rem' }} />
                    <h4 style={{ fontWeight: 700, color: 'var(--success-color)' }}>Payment Confirmed!</h4>
                  </div>
                )}

                {mpesaStatus === 'failed' && (
                  <div style={{ textAlign: 'center', padding: '1rem 0' }}>
                    <AlertCircle size={48} color="#ef4444" style={{ margin: '0 auto 1rem' }} />
                    <p style={{ color: '#ef4444', fontWeight: 600 }}>Payment Failed</p>
                    <button 
                      className="btn btn-secondary" 
                      onClick={() => { setMpesaStatus('idle'); setPaymentError(''); }}
                      style={{ marginTop: '1rem' }}
                    >
                      Try Again
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Paystack Flow */}
            {paymentMethod === 'paystack' && (
              <div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
                  A secure Paystack payment popup will open for the customer to pay <strong>{formatKES(grandTotal)}</strong> via card.
                </p>
                <button 
                  className="btn btn-primary" 
                  onClick={handlePaystackPayment}
                  style={{ 
                    width: '100%', 
                    padding: '1rem', 
                    fontWeight: 600, 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    gap: '0.5rem',
                    background: 'linear-gradient(135deg, #0ea5e9, #0369a1)'
                  }}
                >
                  <CreditCard size={18} />
                  Pay with Card (Paystack)
                </button>
                <div style={{ marginTop: '0.75rem', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>
                  🔒 Secured by Paystack
                </div>
              </div>
            )}

            {/* Error Display */}
            {paymentError && (
              <div style={{ 
                marginTop: '1rem', 
                padding: '0.75rem 1rem', 
                backgroundColor: 'rgba(239, 68, 68, 0.1)', 
                borderRadius: '0.5rem',
                color: '#ef4444',
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <AlertCircle size={16} />
                {paymentError}
              </div>
            )}
          </div>
        </div>
      )}

      {/* --- Success Overlay --- */}
      {orderStatus === 'success' && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.8)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backdropFilter: 'blur(8px)'
        }}>
          <div className="card animate-fade-in" style={{ padding: '3rem', textAlign: 'center', maxWidth: '400px' }}>
            <CheckCircle2 size={64} color="var(--success-color)" style={{ margin: '0 auto 1.5rem' }} />
            <h2 className="heading-2">Sale Complete!</h2>
            <p className="text-secondary" style={{ marginTop: '0.5rem' }}>The order has been synced to the primary database.</p>
          </div>
        </div>
      )}

      {/* --- Failed Overlay --- */}
      {orderStatus === 'failed' && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.8)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backdropFilter: 'blur(8px)'
        }}>
          <div className="card animate-fade-in" style={{ padding: '3rem', textAlign: 'center', maxWidth: '400px' }}>
            <AlertCircle size={64} color="#ef4444" style={{ margin: '0 auto 1.5rem' }} />
            <h2 className="heading-2">Payment Failed</h2>
            <p className="text-secondary" style={{ marginTop: '0.5rem' }}>The transaction could not be completed. Please try again.</p>
          </div>
        </div>
      )}

      {/* --- Camera Scanner Modal --- */}
      {showCameraScanner && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.8)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backdropFilter: 'blur(8px)'
        }}>
          <div className="card animate-fade-in" style={{ padding: '2rem', width: '90%', maxWidth: '400px', position: 'relative' }}>
            <button 
              onClick={() => setShowCameraScanner(false)}
              style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', zIndex: 10 }}
            >
              <X size={20} />
            </button>
            
            <h3 style={{ fontWeight: 600, fontSize: '1.2rem', marginBottom: '1rem', textAlign: 'center' }}>Scan QR / Barcode</h3>
            <div id="qr-reader" style={{ width: '100%' }}></div>
            <p style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-tertiary)', marginTop: '1rem' }}>
              Hold product barcode inside the frame
            </p>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4); }
          50% { box-shadow: 0 0 0 20px rgba(76, 175, 80, 0); }
        }
      `}</style>
    </div>
  );
}
