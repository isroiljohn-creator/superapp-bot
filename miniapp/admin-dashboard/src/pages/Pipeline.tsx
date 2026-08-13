import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
    DndContext, DragEndEvent, DragOverlay, DragStartEvent,
    PointerSensor, useSensor, useSensors, closestCorners,
} from "@dnd-kit/core";
import { useDroppable } from "@dnd-kit/core";
import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { fetchApi } from "@/lib/api";
import DealDetail from "@/components/DealDetail";

interface Deal {
    id: number;
    user_id: number;
    user_name: string | null;
    telegram_id: number;
    stage: string;
    amount: number | null;
    assigned_to: number | null;
    created_at: string;
}

const STAGES = [
    { id: "new", label: "Yangi" },
    { id: "contacted", label: "Bog'lanildi" },
    { id: "offer", label: "Taklif" },
    { id: "won", label: "Yopildi" },
    { id: "lost", label: "Yo'qotildi" },
];

function DealCard({ deal, onClick }: { deal: Deal; onClick: () => void }) {
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({ id: deal.id });
    const style = transform ? { transform: CSS.Translate.toString(transform) } : undefined;

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...listeners}
            {...attributes}
            onClick={onClick}
            className={`glass-card p-3 rounded-lg cursor-grab active:cursor-grabbing text-sm ${isDragging ? "opacity-40" : ""}`}
        >
            <p className="font-medium truncate">{deal.user_name || "Noma'lum"}</p>
            <p className="text-xs text-muted-foreground">#{deal.id} · {deal.telegram_id}</p>
            {deal.amount && (
                <Badge variant="secondary" className="mt-1">{deal.amount.toLocaleString()} so'm</Badge>
            )}
        </div>
    );
}

function StageColumn({ stage, deals, onCardClick }: { stage: { id: string; label: string }; deals: Deal[]; onCardClick: (d: Deal) => void }) {
    const { setNodeRef, isOver } = useDroppable({ id: stage.id });

    return (
        <div
            ref={setNodeRef}
            className={`flex-1 min-w-[240px] rounded-xl p-3 space-y-2 border ${isOver ? "bg-primary/5 border-primary/40" : "border-border"}`}
        >
            <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-sm">{stage.label}</h3>
                <Badge variant="outline">{deals.length}</Badge>
            </div>
            <div className="space-y-2 min-h-[60px]">
                {deals.map((d) => (
                    <DealCard key={d.id} deal={d} onClick={() => onCardClick(d)} />
                ))}
            </div>
        </div>
    );
}

export default function Pipeline() {
    const queryClient = useQueryClient();
    const [activeDeal, setActiveDeal] = useState<Deal | null>(null);
    const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);
    const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

    const { data, isLoading } = useQuery<{ deals: Deal[] }>({
        queryKey: ["crm-deals"],
        queryFn: () => fetchApi("/api/admin/crm/deals"),
    });

    const updateStage = useMutation({
        mutationFn: ({ id, stage }: { id: number; stage: string }) =>
            fetchApi(`/api/admin/crm/deals/${id}`, { method: "PATCH", body: JSON.stringify({ stage }) }),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["crm-deals"] }),
        onError: (e: Error) => toast.error(e.message),
    });

    const deals = data?.deals || [];

    const handleDragStart = (event: DragStartEvent) => {
        const deal = deals.find((d) => d.id === event.active.id);
        setActiveDeal(deal || null);
    };

    const handleDragEnd = (event: DragEndEvent) => {
        setActiveDeal(null);
        const { active, over } = event;
        if (!over) return;
        const deal = deals.find((d) => d.id === active.id);
        const newStage = over.id as string;
        if (deal && deal.stage !== newStage) {
            updateStage.mutate({ id: deal.id, stage: newStage });
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <h2 className="text-xl font-bold">Sotuv Pipeline</h2>
            <DndContext sensors={sensors} collisionDetection={closestCorners} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
                <div className="flex gap-3 overflow-x-auto pb-2">
                    {STAGES.map((stage) => (
                        <StageColumn
                            key={stage.id}
                            stage={stage}
                            deals={deals.filter((d) => d.stage === stage.id)}
                            onCardClick={setSelectedDeal}
                        />
                    ))}
                </div>
                <DragOverlay>
                    {activeDeal ? <DealCard deal={activeDeal} onClick={() => {}} /> : null}
                </DragOverlay>
            </DndContext>

            <DealDetail deal={selectedDeal} open={!!selectedDeal} onClose={() => setSelectedDeal(null)} />
        </div>
    );
}
