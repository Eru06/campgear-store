import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function SsoCallback() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');

    if (!accessToken || !refreshToken) {
      navigate('/login', { replace: true });
      return;
    }

    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);

    refreshUser().then(() => {
      navigate('/admin', { replace: true });
    });
  }, [navigate, refreshUser]);

  return (
    <div className="max-w-md mx-auto mt-16 text-center">
      <p className="text-gray-600">Signing you in...</p>
    </div>
  );
}
