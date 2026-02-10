import { Link } from 'react-router-dom';
import { useCart } from '../context/CartContext';

export default function Cart() {
  const { cart, loading, updateItem, removeItem, clearCart } = useCart();

  if (loading) return <div className="text-center py-12 text-gray-500">Loading cart...</div>;
  if (!cart || cart.items.length === 0) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Your Cart</h1>
        <p className="text-gray-500 mb-4">Your cart is empty.</p>
        <Link to="/" className="text-green-600 hover:underline">Browse products</Link>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Your Cart</h1>
        <button onClick={clearCart} className="text-sm text-red-500 hover:underline">Clear Cart</button>
      </div>

      <div className="space-y-4">
        {cart.items.map((item) => (
          <div key={item.id} className="flex items-center gap-4 bg-white border rounded-lg p-4">
            <div className="flex-1">
              <p className="font-semibold text-gray-800">{item.product_name}</p>
              <p className="text-sm text-gray-500">${Number(item.product_price).toFixed(2)} each</p>
            </div>
            <div className="flex items-center border rounded">
              <button
                onClick={() => item.quantity > 1 ? updateItem(item.id, item.quantity - 1) : removeItem(item.id)}
                className="px-3 py-1 hover:bg-gray-50"
              >
                -
              </button>
              <span className="px-3 py-1 border-x">{item.quantity}</span>
              <button
                onClick={() => updateItem(item.id, item.quantity + 1)}
                className="px-3 py-1 hover:bg-gray-50"
              >
                +
              </button>
            </div>
            <p className="font-semibold text-gray-900 w-24 text-right">${Number(item.subtotal).toFixed(2)}</p>
            <button onClick={() => removeItem(item.id)} className="text-red-400 hover:text-red-600 text-sm">
              Remove
            </button>
          </div>
        ))}
      </div>

      <div className="mt-6 border-t pt-6 flex items-center justify-between">
        <span className="text-xl font-bold text-gray-900">Total: ${Number(cart.total).toFixed(2)}</span>
        <Link
          to="/checkout"
          className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
        >
          Proceed to Checkout
        </Link>
      </div>
    </div>
  );
}
