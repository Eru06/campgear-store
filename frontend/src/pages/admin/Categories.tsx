import { useState, useEffect } from 'react';
import { api, ApiError } from '../../api/client';
import type { CategoryResponse, CategoryCreate } from '../../types';

export default function AdminCategories() {
  const [categories, setCategories] = useState<CategoryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState({ name: '', slug: '', description: '' });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [showNew, setShowNew] = useState(false);

  const fetchCategories = () => {
    setLoading(true);
    api<CategoryResponse[]>('/categories').then(setCategories).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => { fetchCategories(); }, []);

  const autoSlug = (name: string) => name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');

  const handleCreate = async () => {
    setSaving(true);
    setError('');
    try {
      const body: CategoryCreate = { name: form.name, slug: form.slug, description: form.description || undefined };
      await api('/categories', { method: 'POST', body });
      setShowNew(false);
      setForm({ name: '', slug: '', description: '' });
      fetchCategories();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (cat: CategoryResponse) => {
    setEditId(cat.id);
    setForm({ name: cat.name, slug: cat.slug, description: cat.description || '' });
    setError('');
  };

  const handleUpdate = async () => {
    if (!editId) return;
    setSaving(true);
    setError('');
    try {
      await api(`/categories/${editId}`, { method: 'PUT', body: { name: form.name, slug: form.slug, description: form.description || null } });
      setEditId(null);
      fetchCategories();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this category? Products in it will become uncategorized.')) return;
    try {
      await api(`/categories/${id}`, { method: 'DELETE' });
      fetchCategories();
    } catch (err) {
      if (err instanceof ApiError) alert(err.message);
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Categories</h1>
        <button onClick={() => { setShowNew(true); setEditId(null); setForm({ name: '', slug: '', description: '' }); }}
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium">
          + New Category
        </button>
      </div>

      {error && <div className="mb-4 text-red-600 text-sm">{error}</div>}

      {showNew && (
        <div className="mb-4 bg-green-50 border border-green-200 rounded-lg p-4 space-y-3">
          <input placeholder="Name" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value, slug: autoSlug(e.target.value) })}
            className="w-full border rounded px-3 py-2" />
          <input placeholder="Slug" value={form.slug}
            onChange={(e) => setForm({ ...form, slug: e.target.value })}
            className="w-full border rounded px-3 py-2" />
          <input placeholder="Description (optional)" value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="w-full border rounded px-3 py-2" />
          <div className="flex gap-2">
            <button onClick={handleCreate} disabled={saving}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-1 rounded text-sm disabled:bg-green-400">
              {saving ? 'Creating...' : 'Create'}
            </button>
            <button onClick={() => setShowNew(false)} className="px-4 py-1 border rounded text-sm">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white border rounded-lg divide-y">
        {categories.map((cat) => (
          <div key={cat.id} className="p-4">
            {editId === cat.id ? (
              <div className="space-y-2">
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full border rounded px-3 py-1 text-sm" />
                <input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })}
                  className="w-full border rounded px-3 py-1 text-sm" />
                <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Description" className="w-full border rounded px-3 py-1 text-sm" />
                <div className="flex gap-2">
                  <button onClick={handleUpdate} disabled={saving}
                    className="bg-blue-600 text-white px-3 py-1 rounded text-xs disabled:bg-blue-400">
                    {saving ? 'Saving...' : 'Save'}
                  </button>
                  <button onClick={() => setEditId(null)} className="px-3 py-1 border rounded text-xs">Cancel</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-800">{cat.name}</p>
                  <p className="text-xs text-gray-500">{cat.slug}{cat.description ? ` — ${cat.description}` : ''}</p>
                </div>
                <div className="space-x-2">
                  <button onClick={() => startEdit(cat)} className="text-blue-600 hover:underline text-xs">Edit</button>
                  <button onClick={() => handleDelete(cat.id)} className="text-red-500 hover:underline text-xs">Delete</button>
                </div>
              </div>
            )}
          </div>
        ))}
        {categories.length === 0 && (
          <div className="p-4 text-center text-gray-500">No categories yet.</div>
        )}
      </div>
    </div>
  );
}
