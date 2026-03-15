import { useState, useRef, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { HtmlToolbar } from "@/components/ui/html-toolbar";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/components/ui/use-toast";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";
import { Trash2, Edit2, Plus, PlayCircle, Upload, X, Loader2, CheckCircle2 } from "lucide-react";

function getTelegramInitData(): string {
    try {
        if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
            const d = (window as any).Telegram.WebApp.initData;
            if (d && typeof d === "string" && d.length > 0) return d;
        }
    } catch { }
    return "";
}

interface CourseModule {
    id: number;
    title: string;
    description: string | null;
    video_url: string | null;
    video_file_id: string | null;
    channel_message_id: number | null;
    order: number;
    is_active: boolean;
    unlock_condition: string | null;
}

export default function CourseManager() {
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingModule, setEditingModule] = useState<CourseModule | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [videoUploading, setVideoUploading] = useState(false);
    const [videoPreviewName, setVideoPreviewName] = useState<string | null>(null);

    // Form State
    const [formData, setFormData] = useState({
        title: "",
        description: "",
        video_url: "",
        video_file_id: "",
        channel_message_id: "",
        order: 1,
        is_active: true,
    });

    const { data: courses, isLoading } = useQuery<CourseModule[]>({
        queryKey: ["adminCourses"],
        queryFn: () => fetchApi("/api/admin/courses"),
    });

    const createMutation = useMutation({
        mutationFn: (newModule: any) => fetchApi("/api/admin/courses", {
            method: "POST",
            body: JSON.stringify(newModule),
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["adminCourses"] });
            toast({ title: "✅ Muvaffaqiyatli", description: "Dars qo'shildi" });
            setIsModalOpen(false);
        },
        onError: (error: any) => {
            toast({ title: "Xatolik", description: error.message, variant: "destructive" });
        },
    });

    const updateMutation = useMutation({
        mutationFn: (updated: any) => fetchApi(`/api/admin/courses/${updated.id}`, {
            method: "PUT",
            body: JSON.stringify(updated.data),
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["adminCourses"] });
            toast({ title: "✅ Muvaffaqiyatli", description: "Dars yangilandi" });
            setIsModalOpen(false);
        },
        onError: (error: any) => {
            toast({ title: "Xatolik", description: error.message, variant: "destructive" });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: number) => fetchApi(`/api/admin/courses/${id}`, {
            method: "DELETE",
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["adminCourses"] });
            toast({ title: "✅ Muvaffaqiyatli", description: "Dars o'chirildi" });
        },
        onError: (error: any) => {
            toast({ title: "Xatolik", description: error.message, variant: "destructive" });
        },
    });

    // Video upload handler
    const handleVideoUpload = useCallback(async (file: File) => {
        setVideoUploading(true);
        setVideoPreviewName(file.name);
        try {
            const fd = new FormData();
            fd.append("file", file);
            const initData = getTelegramInitData();
            const headers: Record<string, string> = {};
            if (initData) headers["Authorization"] = `tma ${initData}`;

            const res = await fetch("/api/admin/upload-media-form", {
                method: "POST",
                headers,
                body: fd,
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Upload failed: ${res.status}`);
            }
            const data = await res.json();
            setFormData(prev => ({ ...prev, video_file_id: data.file_id }));
            toast({ title: "✅ Video yuklandi", description: "Telegram file_id olindi." });
        } catch (err: any) {
            toast({ title: "Video yuklash xatosi", description: err.message, variant: "destructive" });
            setVideoPreviewName(null);
        } finally {
            setVideoUploading(false);
        }
    }, [toast]);

    const handleOpenModal = (mod: CourseModule | null = null) => {
        if (mod) {
            setEditingModule(mod);
            setFormData({
                title: mod.title || "",
                description: mod.description || "",
                video_url: mod.video_url || "",
                video_file_id: mod.video_file_id || "",
                channel_message_id: mod.channel_message_id ? String(mod.channel_message_id) : "",
                order: mod.order || 1,
                is_active: mod.is_active ?? true,
            });
            setVideoPreviewName(mod.video_file_id ? "Mavjud video ✓" : null);
        } else {
            setEditingModule(null);
            const nextOrder = courses ? courses.length + 1 : 1;
            setFormData({
                title: "",
                description: "",
                video_url: "",
                video_file_id: "",
                channel_message_id: "",
                order: nextOrder,
                is_active: true,
            });
            setVideoPreviewName(null);
        }
        setIsModalOpen(true);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const payload = {
            title: formData.title,
            description: formData.description,
            video_url: formData.video_url,
            video_file_id: formData.video_file_id || null,
            channel_message_id: formData.channel_message_id ? Number(formData.channel_message_id) : null,
            order: Number(formData.order),
            is_active: formData.is_active,
        };

        if (editingModule) {
            updateMutation.mutate({ id: editingModule.id, data: payload });
        } else {
            createMutation.mutate(payload);
        }
    };

    const handleDelete = (id: number) => {
        if (confirm("Rostdan ham ushbu darsni o'chirmoqchimisiz?")) {
            deleteMutation.mutate(id);
        }
    };

    const removeVideo = () => {
        setFormData(prev => ({ ...prev, video_file_id: "" }));
        setVideoPreviewName(null);
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold tracking-tight">📚 Bepul Darslar</h2>
                <Button onClick={() => handleOpenModal()} className="gap-2">
                    <Plus className="w-4 h-4" /> Yangi Dars
                </Button>
            </div>

            <div className="grid gap-4">
                {isLoading ? (
                    <div className="flex justify-center p-8"><span className="animate-spin text-2xl">⏳</span></div>
                ) : courses && courses.length > 0 ? (
                    courses.map((course) => (
                        <Card key={course.id} className={`transition-all duration-200 ${!course.is_active ? 'opacity-60' : ''}`}>
                            <CardContent className="p-4 flex items-center justify-between gap-4">
                                <div className="flex items-center gap-4">
                                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold">
                                        {course.order}
                                    </div>
                                    <div>
                                        <h3 className="font-semibold">{course.title}</h3>
                                        <p className="text-sm text-muted-foreground line-clamp-1">
                                            {course.description || "Ta'rif yo'q"}
                                        </p>
                                        <div className="flex gap-2 mt-1 text-xs items-center text-muted-foreground">
                                            {course.channel_message_id ? (
                                                <span className="flex items-center gap-1 text-blue-500"><PlayCircle className="w-3 h-3" /> Kanal video ✓</span>
                                            ) : course.video_file_id ? (
                                                <span className="flex items-center gap-1 text-green-500"><PlayCircle className="w-3 h-3" /> Video yuklangan ✓</span>
                                            ) : course.video_url ? (
                                                <span className="flex items-center gap-1 text-purple-500"><PlayCircle className="w-3 h-3" /> Tashqi Havola</span>
                                            ) : (
                                                <span className="text-destructive">⚠️ Video yo'q</span>
                                            )}
                                            {!course.is_active && <span className="text-destructive font-semibold px-2">Yashirilgan</span>}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button variant="ghost" size="icon" onClick={() => handleOpenModal(course)}>
                                        <Edit2 className="w-4 h-4" />
                                    </Button>
                                    <Button variant="ghost" size="icon" className="text-destructive hover:bg-destructive/10" onClick={() => handleDelete(course.id)}>
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))
                ) : (
                    <div className="text-center p-8 text-muted-foreground border border-dashed rounded-lg">
                        Hali darslar qo'shilmagan.
                    </div>
                )}
            </div>

            <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>{editingModule ? "Darsni Tahrirlash" : "Yangi Dars Qo'shish"}</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleSubmit} noValidate className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Sarlavha (Title)</Label>
                            <Input value={formData.title} onChange={e => setFormData({ ...formData, title: e.target.value })} placeholder="Misol: 1-dars. Kirish" />
                        </div>

                        {/* Video Upload Section */}
                        <div className="space-y-2">
                            <Label>🎬 Video Darslik</Label>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="video/*"
                                className="hidden"
                                onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    if (file) {
                                        if (file.size > 50 * 1024 * 1024) {
                                            toast({
                                                title: "⚠️ Fayl juda katta",
                                                description: "Telegram limiti: 50MB. Katta videolar uchun URL ishlating.",
                                                variant: "destructive"
                                            });
                                            e.target.value = "";
                                            return;
                                        }
                                        handleVideoUpload(file);
                                    }
                                    e.target.value = "";
                                }}
                            />

                            {/* Show uploaded video */}
                            {formData.video_file_id ? (
                                <div className="flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                                    <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-green-700 dark:text-green-400 truncate">
                                            {videoPreviewName || "Video yuklangan"}
                                        </p>
                                        <p className="text-[10px] text-muted-foreground truncate">
                                            ID: {formData.video_file_id.substring(0, 30)}...
                                        </p>
                                    </div>
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        className="text-destructive hover:bg-destructive/10 flex-shrink-0"
                                        onClick={removeVideo}
                                    >
                                        <X className="w-4 h-4" />
                                    </Button>
                                </div>
                            ) : videoUploading ? (
                                <div className="flex items-center gap-3 p-3 bg-primary/5 border border-primary/20 rounded-lg">
                                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
                                    <div>
                                        <p className="text-sm font-medium">Yuklanmoqda...</p>
                                        <p className="text-[10px] text-muted-foreground">{videoPreviewName}</p>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {/* File upload button */}
                                    <Button
                                        type="button"
                                        variant="outline"
                                        className="w-full h-16 border-dashed border-2 flex flex-col gap-1"
                                        onClick={() => fileInputRef.current?.click()}
                                    >
                                        <Upload className="w-5 h-5 text-muted-foreground" />
                                        <span className="text-xs text-muted-foreground">Galereyadan video tanlang (max 50MB)</span>
                                    </Button>

                                    {/* Video URL input */}
                                    <div className="relative">
                                        <Input
                                            value={formData.video_url}
                                            onChange={e => setFormData({ ...formData, video_url: e.target.value })}
                                            placeholder="🔗 Video URL (YouTube, Drive, Telegram...)"
                                            className="text-sm"
                                        />
                                        {formData.video_url && (
                                            <p className="text-[10px] text-green-500 mt-1">✓ Katta videolar uchun URL ishlatiladi (cheksiz hajm)</p>
                                        )}
                                    </div>
                                    <p className="text-[10px] text-muted-foreground">
                                        💡 50MB dan katta videolar uchun yopiq kanaldan foydalaning
                                    </p>
                                </div>
                            )}
                        </div>

                        {/* Channel Message ID — for private channel videos */}
                        <div className="space-y-2">
                            <Label>📺 Kanal xabar ID (2GB gacha)</Label>
                            <Input
                                type="number"
                                value={formData.channel_message_id}
                                onChange={e => setFormData({ ...formData, channel_message_id: e.target.value })}
                                placeholder="Masalan: 5"
                            />
                            <p className="text-[10px] text-muted-foreground">
                                💡 Yopiq kanalga video yuklang → xabarni forward qiling → ID raqamini bu yerga yozing
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label>Ta'rif (Description)</Label>
                            <HtmlToolbar
                                value={formData.description}
                                onChange={(val) => setFormData({ ...formData, description: val })}
                                placeholder="Dars haqida qisqacha ma'lumot..."
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Tartib raqami</Label>
                                <Input type="number" value={formData.order} onChange={e => setFormData({ ...formData, order: Number(e.target.value) })} />
                            </div>
                            <div className="flex flex-col justify-center space-y-2 pt-6">
                                <div className="flex items-center gap-2">
                                    <Switch checked={formData.is_active} onCheckedChange={c => setFormData({ ...formData, is_active: c })} />
                                    <Label>Aktivmi?</Label>
                                </div>
                            </div>
                        </div>
                        <DialogFooter className="pt-4">
                            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>Bekor qilish</Button>
                            <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending || videoUploading}>
                                {videoUploading ? "Video yuklanmoqda..." : editingModule ? "Saqlash" : "Qo'shish"}
                            </Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Dialog>
        </div>
    );
}
