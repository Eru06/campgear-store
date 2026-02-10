import { useApi } from '../../hooks/useApi';
import { Link } from 'react-router-dom';
import type { PaginatedOrders, OrderStatus } from '../../types';

const STATUS_LABELS: Record<OrderStatus, string> = {
  pending_payment: 'Pending Payment',
  confirmed: 'Confirmed',
  shipped: 'Shipped',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
};

const STATUS_COLORS: Record<OrderStatus, string> = {
  pending_payment: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  confirmed: 'bg-blue-50 border-blue-200 text-blue-800',
  shipped: 'bg-purple-50 border-purple-200 text-purple-800',
  delivered: 'bg-green-50 border-green-200 text-green-800',
  cancelled: 'bg-red-50 border-red-200 text-red-800',
};

export default function AdminDashboard() {
  const { data: orders, loading } = useApi<PaginatedOrders>('/admin/orders', { page: 1, per_page: 100 });

  const statusCounts: Record<string, number> = {};
  if (orders) {
    for (const o of orders.items) {
      statusCounts[o.status] = (statusCounts[o.status] || 0) + 1;
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Admin Dashboard</h1>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            {(Object.keys(STATUS_LABELS) as OrderStatus[]).map((status) => (
              <div key={status} className={`border rounded-lg p-4 ${STATUS_COLORS[status]}`}>
                <p className="text-2xl font-bold">{statusCounts[status] || 0}</p>
                <p className="text-sm">{STATUS_LABELS[status]}</p>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">Recent Orders</h2>
            <p className="text-sm text-gray-500">Total: {orders?.total || 0}</p>
          </div>

          <div className="bg-white border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="px-4 py-3 font-medium">Order ID</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Items</th>
                  <th className="px-4 py-3 font-medium">Total</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {orders?.items.slice(0, 10).map((order) => (
                  <tr key={order.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link to={`/admin/orders/${order.id}`} className="text-green-600 hover:underline">
                        #{order.id.slice(0, 8)}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                        STATUS_COLORS[order.status].replace('bg-', 'bg-').replace('border-', '')
                      }`}>
                        {STATUS_LABELS[order.status]}
                      </span>
                    </td>
                    <td className="px-4 py-3">{order.item_count}</td>
                    <td className="px-4 py-3 font-medium">${Number(order.total).toFixed(2)}</td>
                    <td className="px-4 py-3 text-gray-500">{new Date(order.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6 flex gap-4">
            <Link to="/admin/products" className="text-green-600 hover:underline text-sm">Manage Products &rarr;</Link>
            <Link to="/admin/categories" className="text-green-600 hover:underline text-sm">Manage Categories &rarr;</Link>
            <Link to="/admin/orders" className="text-green-600 hover:underline text-sm">All Orders &rarr;</Link>
            <Link to="/admin/audit-logs" className="text-green-600 hover:underline text-sm">Audit Logs &rarr;</Link>
          </div>
        </>
      )}
    </div>
  );
}
