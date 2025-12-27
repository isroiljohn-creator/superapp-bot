import { useAuth } from '@/hooks/useAuth';
import { AdminDashboard } from '@/components/AdminDashboard';
import { LoadingScreen } from '@/components/LoadingScreen';
import { AccessDenied } from '@/components/AccessDenied';

const Index = () => {
  const { isAuthenticated, isLoading, error } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (error || !isAuthenticated) {
    return <AccessDenied message={error || 'Authentication required'} />;
  }

  return <AdminDashboard />;
};

export default Index;
