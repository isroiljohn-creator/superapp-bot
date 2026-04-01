import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2, Briefcase, Eye, Ban, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { fetchApi } from "@/lib/api";

interface JobVacancy {
    id: number;
    title: string;
    company: string;
    salary: string;
    job_type: string;
    status: string;
    is_active: boolean;
    submitted_by: number;
    channel_msg_id: number | null;
    created_at: string;
}

export default function JobsManager() {
    const queryClient = useQueryClient();

    const { data: jobs = [], isLoading } = useQuery<JobVacancy[]>({
        queryKey: ["admin-jobs"],
        queryFn: () => fetchApi("/api/admin/jobs"),
    });

    const deleteMutation = useMutation({
        mutationFn: (id: number) => fetchApi(`/api/admin/jobs/${id}`, { method: "DELETE" }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-jobs"] });
            toast.success("Vakansiya butunlay o'chirildi");
        },
        onError: (error) => toast.error(error.message),
    });

    const handleDelete = (id: number) => {
        if (confirm("Rostdan ham ushbu vakansiyani o'chirmoqchimisiz? Kanalga tashlangan bo'lsa xabar ham tahrirlanib yopildi deb qoladi.")) {
            deleteMutation.mutate(id);
        }
    };
    
    const formatDate = (dateStr: string) => {
        if (!dateStr) return "Noma'lum";
        const d = new Date(dateStr);
        return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
    }

    const formatStatus = (job: JobVacancy) => {
        if (!job.is_active) {
            return <span className="text-xs bg-red-500/10 text-red-500 px-2 flex items-center gap-1 rounded font-bold"><Ban className="w-3 h-3"/> Yopilgan</span>;
        }
        if (job.status === "approved") {
            return <span className="text-xs bg-green-500/10 text-green-500 px-2 flex items-center gap-1 rounded font-bold"><CheckCircle className="w-3 h-3"/> Tasdiqlangan</span>;
        }
        if (job.status === "rejected") {
            return <span className="text-xs bg-red-500/10 text-red-500 px-2 flex items-center gap-1 rounded font-bold"><Ban className="w-3 h-3"/> Rad etilgan</span>;
        }
        return <span className="text-xs bg-yellow-500/10 text-yellow-500 px-2 flex items-center gap-1 rounded font-bold"><Eye className="w-3 h-3"/> Kutilmoqda</span>;
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold flex items-center gap-2"><Briefcase className="w-6 h-6 text-primary"/> Vakansiyalar</h2>
            </div>

            <div className="bg-primary/10 border border-primary/20 rounded-lg p-3 text-sm flex gap-3 text-primary/80">
                <Briefcase className="h-5 w-5 shrink-0" />
                <p>
                    Bu yerda tizimga kelib tushgan (tasdiqlangan yoki yopilgan) barcha vakansiyalar ro'yxati chiqadi. O'chirish tugmasi ularni bazadan butunlay yo'q qiladi va telegram kanalidagi xabarni "🔴 YOPILDI" deb o'zgartiradi.
                </p>
            </div>

            {isLoading ? (
                <div className="flex justify-center p-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            ) : jobs.length === 0 ? (
                <div className="text-center p-8 border rounded-lg border-dashed text-muted-foreground bg-card/20">
                    <Briefcase className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>Hozircha vakansiyalar yo'q.</p>
                </div>
            ) : (
                <div className="grid gap-3">
                    {jobs.map((job) => (
                        <div key={job.id} className={`glass-card p-4 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all ${!job.is_active ? 'opacity-60 grayscale-[30%]' : ''}`}>
                            <div className="flex gap-4 items-start flex-1 min-w-0">
                                <div className="p-3 rounded-lg shrink-0 bg-primary/10 text-primary border border-primary/20">
                                    <Briefcase className="h-5 w-5" />
                                </div>
                                <div className="flex-1 min-w-0 flex flex-col gap-1">
                                    <div className="flex items-center gap-2">
                                        <h3 className="font-bold text-base truncate text-foreground">
                                            {job.title}
                                        </h3>
                                        {formatStatus(job)}
                                    </div>

                                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground mt-1">
                                        <span className="font-semibold">{job.company || 'Kompaniya raqamsiz'}</span>
                                        <span>•</span>
                                        <span>💰 {job.salary || 'Maosh aytilmagan'}</span>
                                        <span>•</span>
                                        <span className="uppercase">{job.job_type}</span>
                                    </div>

                                    <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground border-t border-border/50 pt-2">
                                        <span>ID: {job.id}</span>
                                        <span>•</span>
                                        <span>Yaratildi: {formatDate(job.created_at)}</span>
                                        <span>•</span>
                                        <span>User ID: {job.submitted_by}</span>
                                        {job.channel_msg_id && (
                                            <>
                                                <span>•</span>
                                                <span className="text-primary font-mono bg-primary/10 px-1 rounded">Xabar: {job.channel_msg_id}</span>
                                            </>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-2 shrink-0 self-end md:self-center mt-2 md:mt-0">
                                <Button 
                                    size="sm" 
                                    variant="destructive" 
                                    className="gap-2"
                                    onClick={() => handleDelete(job.id)}
                                    disabled={deleteMutation.isPending}
                                >
                                    <Trash2 className="h-4 w-4" /> 
                                    <span>O'chirish</span>
                                </Button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
