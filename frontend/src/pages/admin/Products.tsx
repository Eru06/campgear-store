import { useState, useEffect } from 'react';
import { api, ApiError } from '../../api/client';
import type { PaginatedProducts, ProductDetail, ProductCreate, ProductUpdate, CategoryResponse } from '../../types';

export default function AdminProducts() {
  const [products, setProducts] = useState<PaginatedProducts | null>(null);
  const [categories, setCategories] = useState<CategoryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<ProductDetail | null>(null);
  const [form, setForm] = useState({ name: '', slug: '', description: '', price: '', stock: '', category_id: '', is_active: true });
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchProducts = () => {
    setLoading(true);
    api<PaginatedProducts>('/products', { params: { q: search || undefined, page, per_page: 20 } })
      .then(setProducts)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    api<CategoryResponse[]>('/categories').then(setCategories).catch(() => {});
  }, []);

  useEffect(() => { fetchProducts(); }, [page, search]);

  const openCreate = () => {
    setEditing(null);
    setForm({ name: '', slug: '', description: '', price: '', stock: '0', category_id: categories[0]?.id || '', is_active: true });
    setFormError('');
    setShowModal(true);
  };

  const openEdit = async (slug: string) => {
    try {
      const p = await api<ProductDetail>(`/products/${slug}`);
      setEditing(p);
      setForm({
        name: p.name, slug: p.slug, description: p.description || '', price: String(p.price),
        stock: String(p.stock), category_id: p.category.id, is_active: p.is_active,
      });
      setFormError('');
      setShowModal(true);
    } catch { /* */ }
  };

  const handleSave = async () => {
    setSaving(true);
    setFormError('');
    try {
      if (editing) {
        const body: ProductUpdate = {
          name: form.name, slug: form.slug, description: form.description || null,
          price: Number(form.price), stock: Number(form.stock), category_id: form.category_id, is_active: form.is_active,
        };
        await api(`/products/${editing.id}`, { method: 'PUT', body });
      } else {
        const body: ProductCreate = {
          name: form.name, slug: form.slug, description: form.description || undefined,
          price: Number(form.price), stock: Number(form.stock), category_id: form.category_id, is_active: form.is_active,
        };
        await api('/products', { method: 'POST', body });
      }
      setShowModal(false);
      fetchProducts();
    } catch (err) {
      if (err instanceof ApiError) setFormError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Deactivate this product?')) return;
    await api(`/products/${id}`, { method: 'DELETE' });
    fetchProducts();
  };

  const autoSlug = (name: string) => name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Products</h1>
        <button onClick={openCreate} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium">
          + New Product
        </button>
      </div>

      <input
        type="text" placeholder="Search products..." value={search}
        onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        className="w-full border rounded-lg px-4 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-green-500"
      />

      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : (
        <>
          <div className="bg-white border rounded-lg overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Price</th>
                  <th className="px-4 py-3">Stock</th>
                  <th className="px-4 py-3">Active</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {products?.items.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{p.name}</td>
                    <td className="px-4 py-3 text-gray-600">{p.category.name}</td>
                    <td className="px-4 py-3">${Number(p.price).toFixed(2)}</td>
                    <td className="px-4 py-3">{p.stock}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded ${p.stock > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {p.stock > 0 ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td className="px-4 py-3 space-x-2">
                      <button onClick={() => openEdit(p.slug)} className="text-blue-600 hover:underline text-xs">Edit</button>
                      <button onClick={() => handleDelete(p.id)} className="text-red-500 hover:underline text-xs">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {products && products.pages > 1 && (
            <div className="mt-4 flex justify-center gap-2">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
                className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-gray-50">Prev</button>
              <span className="px-3 py-1 text-sm text-gray-600">Page {page} of {products.pages}</span>
              <button onClick={() => setPage((p) => Math.min(products.pages, p + 1))} disabled={page === products.pages}
                className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-gray-50">Next</button>
            </div>
          )}
        </>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">{editing ? 'Edit Product' : 'New Product'}</h2>
            {formError && <div className="mb-3 text-red-600 text-sm">{formError}</div>}
            <div className="space-y-3">
              <input placeholder="Name" value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value, slug: editing ? form.slug : autoSlug(e.target.value) })}
                className="w-full border rounded px-3 py-2" />
              <input placeholder="Slug" value={form.slug}
                onChange={(e) => setForm({ ...form, slug: e.target.value })}
                className="w-full border rounded px-3 py-2" />
              <textarea placeholder="Description" value={form.description} rows={3}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="w-full border rounded px-3 py-2" />
              <div className="grid grid-cols-2 gap-3">
                <input placeholder="Price" type="number" step="0.01" value={form.price}
                  onChange={(e) => setForm({ ...form, price: e.target.value })}
                  className="border rounded px-3 py-2" />
                <input placeholder="Stock" type="number" value={form.stock}
                  onChange={(e) => setForm({ ...form, stock: e.target.value })}
                  className="border rounded px-3 py-2" />
              </div>
              <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}
                className="w-full border rounded px-3 py-2">
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
                Active
              </label>
            </div>
            <div className="mt-4 flex justify-end gap-3">
              <button onClick={() => setShowModal(false)} className="px-4 py-2 border rounded text-sm">Cancel</button>
              <button onClick={handleSave} disabled={saving}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm disabled:bg-green-400">
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
