import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Search, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

type LeadScore = "hot" | "nurture" | "cold";
type UserStatus = "paid" | "free" | "dropped";

interface MockUser {
  id: number;
  name: string;
  phone: string;
  score: LeadScore;
  status: UserStatus;
  source: string;
  events: { action: string; time: string }[];
}

const mockUsers: MockUser[] = [
  {
    id: 4821, name: "Jasur Karimov", phone: "+998901234567", score: "hot", status: "paid", source: "Instagram", events: [
      { action: "/start", time: "Jan 15, 10:00" }, { action: "Registered", time: "Jan 15, 10:02" },
      { action: "VSL Watched", time: "Jan 15, 10:30" }, { action: "Payment: 97,000 UZS", time: "Jan 15, 11:00" },
    ]
  },
  {
    id: 3192, name: "Dilnoza Rahimova", phone: "+998937654321", score: "nurture", status: "free", source: "Telegram", events: [
      { action: "/start", time: "Jan 14, 08:00" }, { action: "Registered", time: "Jan 14, 08:05" },
      { action: "Lead Magnet Opened", time: "Jan 14, 09:00" },
    ]
  },
  {
    id: 7655, name: "Sardor Tursunov", phone: "+998951112233", score: "cold", status: "dropped", source: "Referral", events: [
      { action: "/start", time: "Jan 13, 14:00" },
    ]
  },
  {
    id: 1028, name: "Madina Yusupova", phone: "+998994445566", score: "hot", status: "paid", source: "Campaign X", events: [
      { action: "/start", time: "Jan 12, 09:00" }, { action: "Registered", time: "Jan 12, 09:03" },
      { action: "VSL Watched", time: "Jan 12, 10:00" }, { action: "Checkout Opened", time: "Jan 12, 10:30" },
      { action: "Payment: 197,000 UZS", time: "Jan 12, 11:00" },
    ]
  },
  {
    id: 9401, name: "Bobur Aliyev", phone: "+998907778899", score: "nurture", status: "free", source: "Instagram", events: [
      { action: "/start", time: "Jan 11, 16:00" }, { action: "Registered", time: "Jan 11, 16:05" },
      { action: "Segmented", time: "Jan 11, 16:10" },
    ]
  },
];

const scoreColors: Record<LeadScore, string> = {
  hot: "bg-destructive/10 text-destructive",
  nurture: "bg-warning/10 text-warning",
  cold: "bg-muted text-muted-foreground",
};

const statusColors: Record<UserStatus, string> = {
  paid: "bg-success/10 text-success",
  free: "bg-primary/10 text-primary",
  dropped: "bg-destructive/10 text-destructive",
};

export default function UsersCRM() {
  const [search, setSearch] = useState("");
  const [filterScore, setFilterScore] = useState<LeadScore | "all">("all");
  const [selectedUser, setSelectedUser] = useState<MockUser | null>(null);

  const filtered = mockUsers.filter((u) => {
    const matchSearch = u.name.toLowerCase().includes(search.toLowerCase()) || u.id.toString().includes(search);
    const matchScore = filterScore === "all" || u.score === filterScore;
    return matchSearch && matchScore;
  });

  return (
    <div className="space-y-4">
      <h2 className="text-base font-bold">Foydalanuvchilar (CRM)</h2>

      {/* Search & Filters */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Foydalanuvchini izlash..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 h-9 text-xs bg-secondary border-border/30"
          />
        </div>
      </div>

      <div className="flex gap-1.5">
        {(["all", "hot", "nurture", "cold"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setFilterScore(s)}
            className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors ${filterScore === s ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
              }`}
          >
            {s === "all" ? "Barchasi" : s === "hot" ? "Issiq" : s === "nurture" ? "Iliq" : "Sovuq"}
          </button>
        ))}
      </div>

      {/* User List */}
      <div className="space-y-2">
        {filtered.map((user) => (
          <Card
            key={user.id}
            className="glass-card border-border/30 cursor-pointer hover:border-primary/30 transition-colors"
            onClick={() => setSelectedUser(user)}
          >
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold">{user.name}</p>
                  <p className="text-[10px] text-muted-foreground">#{user.id} · {user.source}</p>
                </div>
                <div className="flex gap-1.5">
                  <Badge variant="secondary" className={`text-[10px] px-1.5 py-0 ${scoreColors[user.score]}`}>
                    {user.score === "hot" ? "issiq" : user.score === "nurture" ? "iliq" : "sovuq"}
                  </Badge>
                  <Badge variant="secondary" className={`text-[10px] px-1.5 py-0 ${statusColors[user.status]}`}>
                    {user.status === "paid" ? "to'lagan" : user.status === "free" ? "bepul" : "tark etgan"}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
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
              className="w-full max-h-[80vh] bg-card border-t border-border rounded-t-2xl p-4 overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-bold">{selectedUser.name}</h3>
                  <p className="text-xs text-muted-foreground">{selectedUser.phone} · {selectedUser.source}</p>
                </div>
                <button onClick={() => setSelectedUser(null)} className="p-1 rounded-full hover:bg-secondary">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="flex gap-2 mb-4">
                <Badge className={`${scoreColors[selectedUser.score]}`}>{selectedUser.score === "hot" ? "issiq" : selectedUser.score === "nurture" ? "iliq" : "sovuq"}</Badge>
                <Badge className={`${statusColors[selectedUser.status]}`}>{selectedUser.status === "paid" ? "to'lagan" : selectedUser.status === "free" ? "bepul" : "tark etgan"}</Badge>
              </div>

              <h4 className="text-sm font-semibold mb-2">Bosib o'tgan yo'li</h4>
              <div className="relative pl-4 border-l-2 border-primary/30 space-y-3">
                {selectedUser.events.map((ev, i) => (
                  <div key={i} className="relative">
                    <div className="absolute -left-[calc(1rem+5px)] top-1 w-2 h-2 rounded-full bg-primary" />
                    <p className="text-xs font-medium">{ev.action}</p>
                    <p className="text-[10px] text-muted-foreground">{ev.time}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
