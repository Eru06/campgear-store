import { useParams, Link } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import type { OrderResponse, OrderStatus } from '../types';

const STATUS_COLORS: Record<OrderStatus, string> = {
  pending_payment: 'bg-yellow-100 text-yellow-800',
  placed: 'bg-blue-100 text-blue-800',
  processing: 'bg-indigo-100 text-indigo-800',
  shipped: 'bg-purple-100 text-purple-800',
  delivered: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
};

const STATUS_LABELS: Record<OrderStatus, string> = {
  pending_payment: 'Pending Payment',
  placed: 'Placed',
  processing: 'Processing',
  shipped: 'Shipped',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
};

const STATUS_STEPS: OrderStatus[] = ['pending_payment', 'placed', 'processing', 'shipped', 'delivered'];

export default function OrderDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: order, loading, error } = useApi<OrderResponse>(`/orders/${id}`);

  if (loading) return <div className="text-center py-12 text-gray-500">Loading order...</div>;
  if (error || !order) return <div className="text-center py-12 text-red-500">Order not found.</div>;

  const currentStep = STATUS_STEPS.indexOf(order.status);

  return (
    <div>
      <Link to="/orders" className="text-green-600 hover:underline text-sm">&larr; Back to orders</Link>

      <div className="mt-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Order #{order.id.slice(0, 8)}</h1>
        <span className={`px-3 py-1 rounded text-sm font-medium ${STATUS_COLORS[order.status]}`}>
          {STATUS_LABELS[order.status]}
        </span>
      </div>

      {order.status !== 'cancelled' && (
        <div className="mt-6 flex items-center gap-1">
          {STATUS_STEPS.map((step, i) => (
            <div key={step} className="flex-1">
              <div className={`h-2 rounded-full ${i <= currentStep ? 'bg-green-500' : 'bg-gray-200'}`} />
              <p className="text-xs text-gray-500 mt-1">{STATUS_LABELS[step]}</p>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 grid md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Items</h2>
          <div className="bg-white border rounded-lg divide-y">
            {order.items.map((item) => (
              <div key={item.id} className="p-4 flex justify-between">
                <div>
                  <p className="font-medium text-gray-800">{item.product_name}</p>
                  <p className="text-sm text-gray-500">${Number(item.unit_price).toFixed(2)} x {item.quantity}</p>
                </div>
                <p className="font-semibold">${(Number(item.unit_price) * item.quantity).toFixed(2)}</p>
              </div>
            ))}
            <div className="p-4 flex justify-between font-bold">
              <span>Total</span>
              <span>${Number(order.total).toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Shipping</h2>
          <div className="bg-white border rounded-lg p-4 space-y-2 text-sm">
            <p><span className="font-medium">Name:</span> {order.shipping_name}</p>
            <p><span className="font-medium">Address:</span> {order.shipping_address}</p>
            <p><span className="font-medium">City:</span> {order.shipping_city}</p>
            <p><span className="font-medium">ZIP:</span> {order.shipping_zip}</p>
            <p><span className="font-medium">Payment:</span> {order.payment_method}</p>
            {order.payment_note && <p><span className="font-medium">Note:</span> {order.payment_note}</p>}
            <p><span className="font-medium">Placed:</span> {new Date(order.created_at).toLocaleString()}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
