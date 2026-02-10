import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { api, ApiError } from '../api/client';
import type { CartResponse } from '../types';
import { useAuth } from './AuthContext';

interface CartState {
  cart: CartResponse | null;
  cartCount: number;
  loading: boolean;
  addItem: (productId: string, quantity?: number) => Promise<void>;
  updateItem: (itemId: string, quantity: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;
  refreshCart: () => Promise<void>;
}

const CartContext = createContext<CartState | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const { isLoggedIn } = useAuth();
  const [cart, setCart] = useState<CartResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchCart = useCallback(async () => {
    if (!isLoggedIn) {
      setCart(null);
      return;
    }
    setLoading(true);
    try {
      const data = await api<CartResponse>('/cart');
      setCart(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setCart(null);
      }
    } finally {
      setLoading(false);
    }
  }, [isLoggedIn]);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const addItem = async (productId: string, quantity = 1) => {
    const data = await api<CartResponse>('/cart/items', {
      method: 'POST',
      body: { product_id: productId, quantity },
    });
    setCart(data);
  };

  const updateItem = async (itemId: string, quantity: number) => {
    const data = await api<CartResponse>(`/cart/items/${itemId}`, {
      method: 'PUT',
      body: { quantity },
    });
    setCart(data);
  };

  const removeItem = async (itemId: string) => {
    const data = await api<CartResponse>(`/cart/items/${itemId}`, {
      method: 'DELETE',
    });
    setCart(data);
  };

  const clearCart = async () => {
    await api('/cart', { method: 'DELETE' });
    setCart(null);
  };

  const cartCount = cart?.items.reduce((sum, i) => sum + i.quantity, 0) ?? 0;

  return (
    <CartContext.Provider
      value={{ cart, cartCount, loading, addItem, updateItem, removeItem, clearCart, refreshCart: fetchCart }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be used within CartProvider');
  return ctx;
}
