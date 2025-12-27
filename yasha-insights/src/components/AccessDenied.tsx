import { ShieldX } from 'lucide-react';

interface AccessDeniedProps {
  message?: string;
}

export function AccessDenied({
  message = 'You do not have permission to access this dashboard.',
}: AccessDeniedProps) {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="text-center max-w-md animate-fade-in">
        <div className="w-20 h-20 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-6">
          <ShieldX className="h-10 w-10 text-destructive" />
        </div>
        <h1 className="text-2xl font-bold mb-3">Access Denied</h1>
        <p className="text-muted-foreground mb-6 whitespace-pre-wrap">{message}</p>
        <p className="text-xs text-muted-foreground/60">
          Error Code: 403 Forbidden
        </p>
      </div>
    </div>
  );
}

export default AccessDenied;
