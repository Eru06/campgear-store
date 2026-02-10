import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import type { ProductDetail as ProductDetailType } from '../types';

export default function ProductDetail() {
  const { slug } = useParams<{ slug: string }>();
  const { data: product, loading, error } = useApi<ProductDetailType>(`/products/${slug}`);
  const { isLoggedIn } = useAuth();
  const { addItem } = useCart();
  const [qty, setQty] = useState(1);
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);

  const handleAdd = async () => {
    if (!product) return;
    setAdding(true);
    try {
      await addItem(product.id, qty);
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    } catch { /* */ }
    setAdding(false);
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;
  if (error || !product) return <div className="text-center py-12 text-red-500">Product not found.</div>;

  return (
    <div>
      <Link to="/" className="text-green-600 hover:underline text-sm">&larr; Back to products</Link>

      <div className="mt-4 grid md:grid-cols-2 gap-8">
        <div className="bg-gray-100 rounded-lg h-80 flex items-center justify-center text-gray-400">
          {product.images.length > 0 ? (
            <img src={product.images[0].url} alt={product.images[0].alt_text || product.name} className="h-full w-full object-cover rounded-lg" />
          ) : (
            <svg className="w-24 h-24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          )}
        </div>

        <div>
          <p className="text-sm text-green-600 font-medium">{product.category.name}</p>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">{product.name}</h1>
          <p className="text-3xl font-bold text-gray-900 mt-4">${Number(product.price).toFixed(2)}</p>

          <div className="mt-2">
            {product.stock > 0 ? (
              <span className="text-green-600 text-sm font-medium">{product.stock} in stock</span>
            ) : (
              <span className="text-red-500 text-sm font-medium">Out of stock</span>
            )}
          </div>

          {product.description && (
            <p className="mt-4 text-gray-600 leading-relaxed">{product.description}</p>
          )}

          {isLoggedIn && product.stock > 0 && (
            <div className="mt-6 flex items-center gap-4">
              <div className="flex items-center border rounded-lg">
                <button
                  onClick={() => setQty((q) => Math.max(1, q - 1))}
                  className="px-3 py-2 hover:bg-gray-50"
                >
                  -
                </button>
                <span className="px-4 py-2 border-x">{qty}</span>
                <button
                  onClick={() => setQty((q) => Math.min(product.stock, q + 1))}
                  className="px-3 py-2 hover:bg-gray-50"
                >
                  +
                </button>
              </div>
              <button
                onClick={handleAdd}
                disabled={adding}
                className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white py-2 rounded-lg font-medium transition-colors"
              >
                {added ? 'Added to Cart!' : adding ? 'Adding...' : 'Add to Cart'}
              </button>
            </div>
          )}

          {!isLoggedIn && (
            <p className="mt-6 text-sm text-gray-500">
              <Link to="/login" className="text-green-600 hover:underline">Log in</Link> to add items to your cart.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
