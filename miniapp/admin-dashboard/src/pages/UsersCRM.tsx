import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Search, X, UserCheck, UserX, ArrowUpDown, Download } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

type LeadScore = "hot" | "nurture" | "cold";
type UserStatusLabel = "paid" | "registered" | "started";
type ActiveTab = "all" | "active" | "inactive";
type SortKey = "date_desc" | "date_asc" | "score_desc" | "source";

interface CRMUser {
  id: number;
  name: string;
  username: string;
  phone: string;
  score: LeadScore;
  status: UserStatusLabel;
  userStatus: string;
  isActive: boolean;
  source: string;
  campaign: string;
  leadScore: number;
  registeredAt: string;
  createdAt: string;
  events: { action: string; time: string }[];
}

const scoreColors: Record<LeadScore, string> = {
  hot: "bg-destructive/10 text-destructive",
  nurture: "bg-warning/10 text-warning",
  cold: "bg-muted text-muted-foreground",
};

const statusColors: Record<UserStatusLabel, string> = {
  paid: "bg-success/10 text-success",
  registered: "bg-primary/10 text-primary",
  started: "bg-warning/10 text-warning",
};

const scoreLabel: Record<LeadScore, string> = {
  hot: "Issiq",
  nurture: "Iliq",
  cold: "Sovuq",
};

const statusLabel: Record<UserStatusLabel, string> = {
  paid: "To'lagan",
  registered: "Ro'yxatli",
  started: "Kutilmoqda",
};

const sortOptions: { id: SortKey; label: string }[] = [
  { id: "date_desc", label: "Yangi → Eski" },
  { id: "date_asc", label: "Eski → Yangi" },
  { id: "score_desc", label: "Ball bo'yicha" },
  { id: "source", label: "Manba bo'yicha" },
];

const TABS: { id: ActiveTab; label: string; icon: React.ElementType }[] = [
  { id: "all", label: "Barchasi", icon: Search },
  { id: "active", label: "Aktiv", icon: UserCheck },
  { id: "inactive", label: "Noaktiv", icon: UserX },
];

export default function UsersCRM() {
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState<ActiveTab>("all");
  const [filterScore, setFilterScore] = useState<LeadScore | "all">("all");
  const [sortKey, setSortKey] = useState<SortKey>("date_desc");
  const [selectedUser, setSelectedUser] = useState<CRMUser | null>(null);

  const { data: usersData, isLoading } = useQuery<CRMUser[]>({
    queryKey: ["admin_users", activeTab, sortKey],
    queryFn: () => fetchApi(`/api/admin/users?status=${activeTab}&sort=${sortKey}`),
    refetchInterval: 30_000,
  });

  // Lazy load events when user is selected
  const { data: userEvents } = useQuery<{ action: string; time: string }[]>({
    queryKey: ["user_events", selectedUser?.id],
    queryFn: () => fetchApi(`/api/admin/users/${selectedUser!.id}/events`),
    enabled: !!selectedUser,
  });

  const users = usersData || [];

  const filtered = users.filter((u) => {
    const matchSearch =
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.id.toString().includes(search) ||
      u.phone.includes(search) ||
      (u.username && u.username.toLowerCase().includes(search.toLowerCase()));
    const matchScore = filterScore === "all" || u.score === filterScore;
    return matchSearch && matchScore;
  });

  const handleExportCSV = async () => {
    try {
      const initData = (window as any).Telegram?.WebApp?.initData || "";
      const baseUrl = import.meta.env.VITE_API_URL || "";
      const res = await fetch(`${baseUrl}/api/admin/users/export?initData=${encodeURIComponent(initData)}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "users_export.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("CSV export error:", e);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold">Userlar (CRM)</h2>
        <button
          onClick={handleExportCSV}
          className="flex items-center gap-1 px-2 py-1 text-[10px] font-medium bg-primary/10 text-primary rounded-md hover:bg-primary/20 transition-colors"
        >
          <Download className="h-3 w-3" />
          CSV
        </button>
      </div>

      {/* Active / Inactive Tabs */}
      <div className="flex gap-1 p-0.5 bg-secondary rounded-lg">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center gap-0.5 py-1 rounded-md text-[10px] font-medium transition-all ${activeTab === tab.id
              ? "bg-card shadow text-foreground"
              : "text-muted-foreground"
              }`}
          >
            <tab.icon className="h-2.5 w-2.5" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Stats bar */}
      {!isLoading && (
        <div className="flex gap-1.5">
          <div className="flex-1 bg-secondary/50 rounded-md px-2 py-1 text-center">
            <p className="text-sm font-bold">{filtered.length}</p>
            <p className="text-[9px] text-muted-foreground">Natija</p>
          </div>
          <div className="flex-1 bg-secondary/50 rounded-md px-2 py-1 text-center">
            <p className="text-sm font-bold text-success">{filtered.filter(u => u.status === "registered").length}</p>
            <p className="text-[9px] text-muted-foreground">Ro'yxatli</p>
          </div>
          <div className="flex-1 bg-secondary/50 rounded-md px-2 py-1 text-center">
            <p className="text-sm font-bold text-warning">{filtered.filter(u => u.status === "started").length}</p>
            <p className="text-[9px] text-muted-foreground">Kutilmoqda</p>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
        <Input
          placeholder="Ism, ID, @username..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-7 h-7 text-[11px] bg-secondary border-border/30"
        />
      </div>

      {/* Sort + Score filters in one row */}
      <div className="flex gap-1.5 items-center">
        <select
          value={sortKey}
          onChange={(e) => setSortKey(e.target.value as SortKey)}
          className="bg-secondary text-foreground text-[10px] rounded-md px-1.5 py-1 border border-border/30 w-24"
        >
          {sortOptions.map((opt) => (
            <option key={opt.id} value={opt.id}>{opt.label}</option>
          ))}
        </select>
        <div className="flex gap-0.5 flex-1">
          {(["all", "hot", "nurture", "cold"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setFilterScore(s)}
              className={`px-1.5 py-0.5 text-[9px] font-medium rounded transition-colors whitespace-nowrap ${filterScore === s
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground"
                }`}
            >
              {s === "all" ? "Barcha" : scoreLabel[s]}
            </button>
          ))}
        </div>
      </div>

      {/* User List */}
      <div className="space-y-2">
        {isLoading ? (
          <div className="text-xs text-muted-foreground text-center p-6">Yuklanmoqda...</div>
        ) : filtered.length === 0 ? (
          <div className="text-xs text-muted-foreground text-center p-6">
            Foydalanuvchilar topilmadi
          </div>
        ) : (
          filtered.map((user) => (
            <Card
              key={user.id}
              className="glass-card border-border/30 cursor-pointer hover:border-primary/30 transition-colors"
              onClick={() => setSelectedUser(user)}
            >
              <CardContent className="p-3">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${user.isActive ? "bg-green-500" : "bg-red-400"}`} />
                      <p className="text-sm font-semibold truncate">{user.name}</p>
                      {user.username && (
                        <span className="text-[10px] text-primary/70 truncate">@{user.username}</span>
                      )}
                    </div>
                    <p className="text-[10px] text-muted-foreground ml-3 truncate">
                      {user.source} · {user.createdAt}
                      {user.campaign && ` · ${user.campaign}`}
                    </p>
                  </div>
                  <div className="flex gap-1 ml-2 flex-shrink-0">
                    <Badge variant="secondary" className={`text-[9px] px-1.5 py-0 ${statusColors[user.status]}`}>
                      {user.status === "paid" ? "To'lagan" : user.status === "registered" ? "Ro'yxatdan ✓" : "O'tmagan"}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* User Profile Modal */}
      <AnimatePresence>
        {selectedUser && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-end"
            onClick={() => setSelectedUser(null)}
          >
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="w-full max-h-[85vh] bg-card border-t border-border rounded-t-2xl p-4 overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${selectedUser.isActive ? "bg-green-500" : "bg-red-400"}`} />
                    <h3 className="text-base font-bold truncate">{selectedUser.name}</h3>
                  </div>
                  <div className="text-xs text-muted-foreground ml-5 space-y-0.5">
                    {selectedUser.username && <p>@{selectedUser.username}</p>}
                    <p>{selectedUser.phone} · {selectedUser.source} · {selectedUser.createdAt}</p>
                    {selectedUser.campaign && <p>Kampaniya: {selectedUser.campaign}</p>}
                  </div>
                </div>
                <button onClick={() => setSelectedUser(null)} className="p-1 rounded-full hover:bg-secondary flex-shrink-0">
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Badges */}
              <div className="flex flex-wrap gap-1.5 mb-4">
                <Badge className={scoreColors[selectedUser.score]}>{scoreLabel[selectedUser.score]}</Badge>
                <Badge className={statusColors[selectedUser.status]}>{statusLabel[selectedUser.status]}</Badge>
                <Badge className={selectedUser.isActive ? "bg-success/10 text-success" : "bg-destructive/10 text-destructive"}>
                  {selectedUser.isActive ? "Aktiv" : "Noaktiv"}
                </Badge>
                <Badge className="bg-muted text-muted-foreground">
                  Ball: {selectedUser.leadScore}
                </Badge>
              </div>

              {/* User Journey Timeline */}
              <h4 className="text-[11px] font-semibold mb-1.5">Bosib o'tgan yo'li</h4>
              {!userEvents ? (
                <div className="text-[10px] text-muted-foreground text-center py-3 mb-3">Yuklanmoqda…</div>
              ) : userEvents.length > 0 ? (
                <div className="relative pl-3 border-l-2 border-primary/30 space-y-2 mb-3">
                  {userEvents.map((ev, i) => {
                    const isLast = i === userEvents.length - 1;
                    return (
                      <div key={i} className="relative">
                        <div className={`absolute -left-[calc(0.75rem+4px)] top-0.5 w-2 h-2 rounded-full ${isLast ? "bg-primary ring-2 ring-primary/30" : "bg-primary/60"}`} />
                        <p className={`text-[11px] ${isLast ? "font-bold" : "font-medium text-foreground/80"}`}>
                          {ev.action}
                        </p>
                        <p className="text-[9px] text-muted-foreground">{ev.time}</p>
                      </div>
                    );
                  })}
                  <div className="relative">
                    <div className="absolute -left-[calc(0.75rem+4px)] top-0.5 w-2 h-2 rounded-full bg-red-400 ring-2 ring-red-400/30 animate-pulse" />
                    <p className="text-[10px] font-bold text-destructive">Shu yerda to'xtagan</p>
                  </div>
                </div>
              ) : (
                <div className="text-[10px] text-muted-foreground text-center py-3 mb-3 border border-dashed border-border rounded-md">
                  Hozircha faollik yo'q
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
