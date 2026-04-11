import { useState, useEffect } from "react";
import { API_URL, fetchApi, getInitData } from "@/lib/api";
import { Loader2, Lock } from "lucide-react";
import { toast } from "sonner";

export default function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [checkingTelegram, setCheckingTelegram] = useState(true);

  // Auto-login if Telegram WebApp initData is present
  useEffect(() => {
    const initData = getInitData();
    if (initData && !localStorage.getItem("admin_token")) {
      // If we have Telegram token, we implicitly assume we are authenticating via Telegram
      // You could still verify it via an endpoint, but fetchApi does it natively.
      onLogin();
    } else if (localStorage.getItem("admin_token")) {
      onLogin();
    }
    setCheckingTelegram(false);
  }, [onLogin]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;
    
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Tizimga kirishda xatolik");
      
      localStorage.setItem("admin_token", data.token);
      toast.success("Muvaffaqiyatli kirdingiz!");
      onLogin();
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (checkingTelegram) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="max-w-md w-full bg-card border border-border/40 rounded-2xl p-8 shadow-xl">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
            <Lock className="w-8 h-8 text-primary" />
          </div>
        </div>
        
        <h2 className="text-2xl font-bold text-center text-foreground mb-2">
          Admin Panelga Kirish
        </h2>
        <p className="text-sm text-center text-muted-foreground mb-8">
          Tizimga kirish uchun login va parolingizni kiriting
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">Login</label>
            <input 
              type="text" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-secondary/50 border border-border/50 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-foreground"
              placeholder="admin"
              required
            />
          </div>
          
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">Parol</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-secondary/50 border border-border/50 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-foreground"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-primary-foreground font-medium rounded-lg px-4 py-2.5 mt-2 transition-all hover:bg-primary/90 flex items-center justify-center"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Kirish"}
          </button>
        </form>
      </div>
    </div>
  );
}
