import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Send, Image, Plus, ChevronDown, ChevronUp } from "lucide-react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface AudienceCount {
  all: number;
  video_not_paid: number;
  hot: number;
  paid: number;
}

interface PastBroadcast {
  id: number;
  title: string;
  sent: number;
  delivered: number;
  status: string;
  date: string;
}

const AUDIENCE_LABELS = [
  { label: "Barcha foydalanuvchilar", key: "all" as keyof AudienceCount },
  { label: "Videoni ko'rgan, lekin to'lamagan", key: "video_not_paid" as keyof AudienceCount },
  { label: "Faqat issiq mijozlar", key: "hot" as keyof AudienceCount },
  { label: "To'lagan mijozlar", key: "paid" as keyof AudienceCount },
];

export default function Broadcast() {
  const [selectedAudience, setSelectedAudience] = useState(0);
  const [message, setMessage] = useState("");
  const [expandedBroadcast, setExpandedBroadcast] = useState<number | null>(null);
  const { toast } = useToast();

  // Fetch audience counts
  const { data: audienceCounts } = useQuery<AudienceCount>({
    queryKey: ["audience_counts"],
    queryFn: () => fetchApi("/api/admin/audience-counts"),
  });

  // Fetch past broadcasts
  const { data: broadcastHistory, refetch: refetchHistory } = useQuery<PastBroadcast[]>({
    queryKey: ["broadcast_history"],
    queryFn: () => fetchApi("/api/admin/broadcasts"),
  });

  const sendBroadcast = useMutation({
    mutationFn: async (payload: { audience: number; message: string }) => {
      return fetchApi("/api/admin/broadcast", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: (data) => {
      toast({
        title: "Xabar yuborildi!",
        description: data.message || "Xabarlarni tarqatish navbatga qo'yildi.",
      });
      setMessage("");
      refetchHistory();
    },
    onError: (error: Error) => {
      toast({
        title: "Xatolik",
        description: error.message || "Xabarni yuborishda xatolik yuz berdi.",
        variant: "destructive",
      });
    },
  });

  const handleSend = () => {
    if (!message.trim()) return;
    sendBroadcast.mutate({ audience: selectedAudience, message: message.trim() });
  };

  const getCount = (key: keyof AudienceCount) => {
    return audienceCounts?.[key] ?? "...";
  };

  return (
    <div className="space-y-4">
      <h2 className="text-base font-bold">Xabarlar yuborish</h2>

      {/* Composer */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3 space-y-3">
          <h3 className="text-sm font-semibold">Yangi xabar</h3>

          {/* Audience */}
          <div>
            <p className="text-[11px] text-muted-foreground mb-1.5">Auditoriya</p>
            <div className="flex flex-wrap gap-1.5">
              {AUDIENCE_LABELS.map((a, i) => (
                <button
                  key={a.key}
                  onClick={() => setSelectedAudience(i)}
                  className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors ${selectedAudience === i
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-secondary-foreground"
                    }`}
                >
                  {a.label} ({getCount(a.key).toLocaleString()})
                </button>
              ))}
            </div>
          </div>

          {/* Message input */}
          <div>
            <textarea
              placeholder="Xabaringizni yozing..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="w-full h-24 text-xs bg-secondary border border-border/30 rounded-lg p-2.5 resize-none focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/30">
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="h-8 text-xs gap-1">
                <Image className="h-3.5 w-3.5" />
                Media
              </Button>
              <Button variant="outline" size="sm" className="h-8 text-xs gap-1">
                <Plus className="h-3.5 w-3.5" />
                Tugma
              </Button>
            </div>
            <Button
              size="sm"
              className="h-8 text-xs gap-1"
              disabled={!message.trim() || sendBroadcast.isPending}
              onClick={handleSend}
            >
              <Send className="h-3.5 w-3.5" />
              {sendBroadcast.isPending ? "Yuborilmoqda..." : "Yuborish"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Past Broadcasts */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <h3 className="text-sm font-semibold mb-3">Avvalgi xabarlar</h3>
          <div className="space-y-2">
            {!broadcastHistory ? (
              <div className="text-xs text-muted-foreground text-center py-2">Yuklanmoqda...</div>
            ) : broadcastHistory.length === 0 ? (
              <div className="text-xs text-muted-foreground text-center py-2">Hozircha xabar yuborilmagan</div>
            ) : (
              broadcastHistory.map((b) => (
                <div key={b.id} className="border border-border/30 rounded-lg p-2.5">
                  <button
                    className="w-full flex items-center justify-between"
                    onClick={() => setExpandedBroadcast(expandedBroadcast === b.id ? null : b.id)}
                  >
                    <div className="text-left">
                      <p className="text-xs font-medium">{b.title}</p>
                      <p className="text-[10px] text-muted-foreground">{b.date}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-[10px] bg-primary/10 text-primary">
                        {b.status}
                      </Badge>
                      {expandedBroadcast === b.id ? (
                        <ChevronUp className="h-3.5 w-3.5 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                      )}
                    </div>
                  </button>
                  {expandedBroadcast === b.id && (
                    <div className="mt-2 pt-2 border-t border-border/30 grid grid-cols-2 gap-2">
                      <div className="text-center">
                        <p className="text-sm font-bold">{b.sent.toLocaleString()}</p>
                        <p className="text-[10px] text-muted-foreground">Yuborildi</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-bold">{b.delivered.toLocaleString()}</p>
                        <p className="text-[10px] text-muted-foreground">Yetkazildi</p>
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
