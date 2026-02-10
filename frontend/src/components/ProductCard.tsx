import { Link } from 'react-router-dom';
import type { ProductListItem } from '../types';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { useState } from 'react';

export default function ProductCard({ product }: { product: ProductListItem }) {
  const { isLoggedIn } = useAuth();
  const { addItem } = useCart();
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);

  const handleAdd = async () => {
    setAdding(true);
    try {
      await addItem(product.id);
      setAdded(true);
      setTimeout(() => setAdded(false), 1500);
    } catch { /* handled by cart context */ }
    setAdding(false);
  };

  return (
    <div className="border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-white">
      <Link to={`/products/${product.slug}`}>
        <div className="bg-gray-100 h-48 flex items-center justify-center text-gray-400">
          {product.thumbnail ? (
            <img src={product.thumbnail} alt={product.name} className="h-full w-full object-cover" />
          ) : (
            <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          )}
        </div>
      </Link>
      <div className="p-4">
        <p className="text-xs text-green-600 font-medium mb-1">{product.category.name}</p>
        <Link to={`/products/${product.slug}`} className="font-semibold text-gray-800 hover:text-green-700 line-clamp-1">
          {product.name}
        </Link>
        <div className="mt-2 flex items-center justify-between">
          <span className="text-lg font-bold text-gray-900">${Number(product.price).toFixed(2)}</span>
          {product.stock > 0 ? (
            <span className="text-xs text-green-600">In Stock</span>
          ) : (
            <span className="text-xs text-red-500">Out of Stock</span>
          )}
        </div>
        {isLoggedIn && product.stock > 0 && (
          <button
            onClick={handleAdd}
            disabled={adding}
            className="mt-3 w-full bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white py-2 rounded text-sm font-medium transition-colors"
          >
            {added ? 'Added!' : adding ? 'Adding...' : 'Add to Cart'}
          </button>
        )}
      </div>
    </div>
  );
}
