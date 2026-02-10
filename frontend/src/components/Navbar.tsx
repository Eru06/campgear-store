import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';

export default function Navbar() {
  const { isLoggedIn, isAdmin, user, logout } = useAuth();
  const { cartCount } = useCart();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <nav className="bg-green-700 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold tracking-tight">
          CampGear
        </Link>

        <div className="flex items-center gap-4">
          <Link to="/" className="hover:text-green-200 transition-colors">
            Products
          </Link>

          {isLoggedIn ? (
            <>
              <Link to="/cart" className="relative hover:text-green-200 transition-colors">
                Cart
                {cartCount > 0 && (
                  <span className="absolute -top-2 -right-4 bg-orange-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {cartCount}
                  </span>
                )}
              </Link>
              <Link to="/orders" className="hover:text-green-200 transition-colors">
                Orders
              </Link>
              {isAdmin && (
                <Link to="/admin" className="hover:text-green-200 transition-colors">
                  Admin
                </Link>
              )}
              <span className="text-green-200 text-sm hidden sm:inline">
                {user?.full_name}
              </span>
              <button
                onClick={handleLogout}
                className="bg-green-800 hover:bg-green-900 px-3 py-1 rounded text-sm transition-colors"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="hover:text-green-200 transition-colors">
                Login
              </Link>
              <Link
                to="/register"
                className="bg-orange-500 hover:bg-orange-600 px-3 py-1 rounded text-sm transition-colors"
              >
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
