import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Save, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { fetchApi } from "@/lib/api";

interface Module {
  badge: string;
  title: string;
  result: string;
  lessons: string[];
  image: string;
}

interface Tier {
  key: string;
  name: string;
  subtitle: string;
  price: string;
  highlight: boolean;
  features: string[];
}

interface FaqItem { q: string; a: string; }
interface ExtraItem { title: string; desc: string; }

interface CourseContent {
  hero: { badge: string; title: string; subtitle: string; cta: string; meta: string[]; image: string };
  audience: { title: string; subtitle: string; items: string[] };
  modules: Module[];
  bonus_title: string;
  bonus_modules: Module[];
  outcomes: { title: string; items: string[] };
  extras: { title: string; items: ExtraItem[]; footer: string };
  pricing: { title: string; tiers: Tier[] };
  faq: FaqItem[];
  lead_form: { title: string; subtitle: string; success: string };
  footer: { text: string };
}

function linesToArr(v: string): string[] {
  return v.split("\n").map((l) => l.trim()).filter(Boolean);
}
function arrToLines(v: string[] | undefined): string {
  return (v || []).join("\n");
}

const emptyModule = (): Module => ({ badge: "", title: "", result: "", lessons: [], image: "" });
const emptyTier = (): Tier => ({ key: "", name: "", subtitle: "", price: "", highlight: false, features: [] });
const emptyFaq = (): FaqItem => ({ q: "", a: "" });
const emptyExtra = (): ExtraItem => ({ title: "", desc: "" });

export default function CourseLandingManager() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery<CourseContent>({
    queryKey: ["admin_course_landing_content"],
    queryFn: () => fetchApi("/api/admin/course-landing/content"),
  });

  const [content, setContent] = useState<CourseContent | null>(null);

  useEffect(() => {
    if (data && !content) setContent(data);
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: (payload: CourseContent) => fetchApi("/api/admin/course-landing/content", { method: "PUT", body: JSON.stringify(payload) }),
    onSuccess: () => {
      toast.success("Saqlandi");
      queryClient.invalidateQueries({ queryKey: ["admin_course_landing_content"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  if (isLoading || !content) {
    return (
      <div className="flex justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  const set = (updater: (c: CourseContent) => CourseContent) => setContent((prev) => (prev ? updater(structuredClone(prev)) : prev));

  return (
    <div className="space-y-4 pb-24">
      <div className="flex items-center justify-between sticky top-0 z-10 bg-background/95 backdrop-blur py-2">
        <div>
          <h2 className="text-xl font-bold">NUVI AI 2.0 — Sayt matni</h2>
          <p className="text-xs text-muted-foreground">nuvi.uz/kurs — har bir matn va rasm shu yerdan boshqariladi</p>
        </div>
        <div className="flex gap-2">
          <a href="/kurs/" target="_blank" rel="noreferrer">
            <Button size="sm" variant="outline" className="gap-2"><ExternalLink className="h-4 w-4" /> Saytni ko'rish</Button>
          </a>
          <Button size="sm" className="gap-2" disabled={saveMutation.isPending} onClick={() => content && saveMutation.mutate(content)}>
            <Save className="h-4 w-4" /> {saveMutation.isPending ? "Saqlanmoqda..." : "Saqlash"}
          </Button>
        </div>
      </div>

      {/* Hero */}
      <Card>
        <CardHeader><CardTitle className="text-base">Hero (bosh qism)</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Field label="Belgi (badge)"><Input value={content.hero.badge} onChange={(e) => set((c) => { c.hero.badge = e.target.value; return c; })} /></Field>
          <Field label="Sarlavha"><Input value={content.hero.title} onChange={(e) => set((c) => { c.hero.title = e.target.value; return c; })} /></Field>
          <Field label="Tavsif"><Textarea rows={3} value={content.hero.subtitle} onChange={(e) => set((c) => { c.hero.subtitle = e.target.value; return c; })} /></Field>
          <Field label="Tugma matni"><Input value={content.hero.cta} onChange={(e) => set((c) => { c.hero.cta = e.target.value; return c; })} /></Field>
          <Field label="Statistika qatorlari (har birini yangi qatorga)">
            <Textarea rows={3} value={arrToLines(content.hero.meta)} onChange={(e) => set((c) => { c.hero.meta = linesToArr(e.target.value); return c; })} />
          </Field>
          <Field label="Hero rasm URL"><Input value={content.hero.image} placeholder="https://..." onChange={(e) => set((c) => { c.hero.image = e.target.value; return c; })} /></Field>
        </CardContent>
      </Card>

      {/* Audience */}
      <Card>
        <CardHeader><CardTitle className="text-base">Kimlar uchun</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Field label="Kichik sarlavha"><Input value={content.audience.subtitle} onChange={(e) => set((c) => { c.audience.subtitle = e.target.value; return c; })} /></Field>
          <Field label="Sarlavha"><Input value={content.audience.title} onChange={(e) => set((c) => { c.audience.title = e.target.value; return c; })} /></Field>
          <Field label="Bandlar (har birini yangi qatorga)">
            <Textarea rows={5} value={arrToLines(content.audience.items)} onChange={(e) => set((c) => { c.audience.items = linesToArr(e.target.value); return c; })} />
          </Field>
        </CardContent>
      </Card>

      <ModuleListEditor
        title="6 ta asosiy modul"
        modules={content.modules}
        onChange={(mods) => set((c) => { c.modules = mods; return c; })}
      />

      <Card>
        <CardHeader><CardTitle className="text-base">Bonus qism sarlavhasi</CardTitle></CardHeader>
        <CardContent>
          <Input value={content.bonus_title} onChange={(e) => set((c) => { c.bonus_title = e.target.value; return c; })} />
        </CardContent>
      </Card>

      <ModuleListEditor
        title="Bonus modullar"
        modules={content.bonus_modules}
        onChange={(mods) => set((c) => { c.bonus_modules = mods; return c; })}
      />

      {/* Outcomes */}
      <Card>
        <CardHeader><CardTitle className="text-base">Natijalar</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Field label="Sarlavha"><Input value={content.outcomes.title} onChange={(e) => set((c) => { c.outcomes.title = e.target.value; return c; })} /></Field>
          <Field label="Bandlar (har birini yangi qatorga)">
            <Textarea rows={6} value={arrToLines(content.outcomes.items)} onChange={(e) => set((c) => { c.outcomes.items = linesToArr(e.target.value); return c; })} />
          </Field>
        </CardContent>
      </Card>

      {/* Extras */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Qo'shimcha imkoniyatlar</CardTitle>
          <Button size="sm" variant="outline" className="gap-1" onClick={() => set((c) => { c.extras.items.push(emptyExtra()); return c; })}>
            <Plus className="h-3.5 w-3.5" /> Qo'shish
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          <Field label="Sarlavha"><Input value={content.extras.title} onChange={(e) => set((c) => { c.extras.title = e.target.value; return c; })} /></Field>
          {content.extras.items.map((it, i) => (
            <div key={i} className="grid grid-cols-[1fr_1fr_auto] gap-2 items-start p-2 rounded-lg bg-secondary/30">
              <Input placeholder="Sarlavha" value={it.title} onChange={(e) => set((c) => { c.extras.items[i].title = e.target.value; return c; })} />
              <Input placeholder="Tavsif" value={it.desc} onChange={(e) => set((c) => { c.extras.items[i].desc = e.target.value; return c; })} />
              <Button size="icon" variant="destructive" onClick={() => set((c) => { c.extras.items.splice(i, 1); return c; })}><Trash2 className="h-4 w-4" /></Button>
            </div>
          ))}
          <Field label="Pastki matn"><Textarea rows={2} value={content.extras.footer} onChange={(e) => set((c) => { c.extras.footer = e.target.value; return c; })} /></Field>
        </CardContent>
      </Card>

      {/* Pricing */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Tariflar</CardTitle>
          <Button size="sm" variant="outline" className="gap-1" onClick={() => set((c) => { c.pricing.tiers.push(emptyTier()); return c; })}>
            <Plus className="h-3.5 w-3.5" /> Tarif qo'shish
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          <Field label="Bo'lim sarlavhasi"><Input value={content.pricing.title} onChange={(e) => set((c) => { c.pricing.title = e.target.value; return c; })} /></Field>
          {content.pricing.tiers.map((t, i) => (
            <div key={i} className="space-y-2 p-3 rounded-lg border border-border">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-muted-foreground">Tarif #{i + 1}</span>
                <Button size="icon" variant="destructive" onClick={() => set((c) => { c.pricing.tiers.splice(i, 1); return c; })}><Trash2 className="h-4 w-4" /></Button>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Field label="Kalit (standard/premium/vip)"><Input value={t.key} onChange={(e) => set((c) => { c.pricing.tiers[i].key = e.target.value; return c; })} /></Field>
                <Field label="Nomi"><Input value={t.name} onChange={(e) => set((c) => { c.pricing.tiers[i].name = e.target.value; return c; })} /></Field>
              </div>
              <Field label="Tavsif"><Input value={t.subtitle} onChange={(e) => set((c) => { c.pricing.tiers[i].subtitle = e.target.value; return c; })} /></Field>
              <div className="grid grid-cols-2 gap-2 items-end">
                <Field label="Narxi (masalan 3 497 000)"><Input value={t.price} onChange={(e) => set((c) => { c.pricing.tiers[i].price = e.target.value; return c; })} /></Field>
                <Button
                  type="button" variant={t.highlight ? "default" : "outline"}
                  onClick={() => set((c) => { c.pricing.tiers[i].highlight = !c.pricing.tiers[i].highlight; return c; })}
                >
                  {t.highlight ? "Ajratilgan ✓" : "Ajratilmagan"}
                </Button>
              </div>
              <Field label="Xususiyatlar (har birini yangi qatorga)">
                <Textarea rows={5} value={arrToLines(t.features)} onChange={(e) => set((c) => { c.pricing.tiers[i].features = linesToArr(e.target.value); return c; })} />
              </Field>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* FAQ */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Savol-javob</CardTitle>
          <Button size="sm" variant="outline" className="gap-1" onClick={() => set((c) => { c.faq.push(emptyFaq()); return c; })}>
            <Plus className="h-3.5 w-3.5" /> Qo'shish
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {content.faq.map((f, i) => (
            <div key={i} className="space-y-2 p-2 rounded-lg bg-secondary/30">
              <div className="flex gap-2 items-center">
                <Input placeholder="Savol" value={f.q} onChange={(e) => set((c) => { c.faq[i].q = e.target.value; return c; })} />
                <Button size="icon" variant="destructive" onClick={() => set((c) => { c.faq.splice(i, 1); return c; })}><Trash2 className="h-4 w-4" /></Button>
              </div>
              <Textarea rows={2} placeholder="Javob" value={f.a} onChange={(e) => set((c) => { c.faq[i].a = e.target.value; return c; })} />
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Lead form + footer */}
      <Card>
        <CardHeader><CardTitle className="text-base">Ariza formasi va footer</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Field label="Forma sarlavhasi"><Input value={content.lead_form.title} onChange={(e) => set((c) => { c.lead_form.title = e.target.value; return c; })} /></Field>
          <Field label="Forma tavsifi"><Textarea rows={2} value={content.lead_form.subtitle} onChange={(e) => set((c) => { c.lead_form.subtitle = e.target.value; return c; })} /></Field>
          <Field label="Muvaffaqiyat xabari"><Textarea rows={2} value={content.lead_form.success} onChange={(e) => set((c) => { c.lead_form.success = e.target.value; return c; })} /></Field>
          <Field label="Footer matni"><Input value={content.footer.text} onChange={(e) => set((c) => { c.footer.text = e.target.value; return c; })} /></Field>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button disabled={saveMutation.isPending} className="gap-2" onClick={() => content && saveMutation.mutate(content)}>
          <Save className="h-4 w-4" /> {saveMutation.isPending ? "Saqlanmoqda..." : "Saqlash"}
        </Button>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-muted-foreground">{label}</label>
      {children}
    </div>
  );
}

function ModuleListEditor({ title, modules, onChange }: { title: string; modules: Module[]; onChange: (m: Module[]) => void }) {
  const update = (i: number, patch: Partial<Module>) => {
    const next = modules.slice();
    next[i] = { ...next[i], ...patch };
    onChange(next);
  };
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base">{title}</CardTitle>
        <Button size="sm" variant="outline" className="gap-1" onClick={() => onChange([...modules, emptyModule()])}>
          <Plus className="h-3.5 w-3.5" /> Modul qo'shish
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {modules.map((m, i) => (
          <div key={i} className="space-y-2 p-3 rounded-lg border border-border">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-muted-foreground">Modul #{i + 1}</span>
              <Button size="icon" variant="destructive" onClick={() => { const next = modules.slice(); next.splice(i, 1); onChange(next); }}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Belgi (masalan 0-Modul)"><Input value={m.badge} onChange={(e) => update(i, { badge: e.target.value })} /></Field>
              <Field label="Sarlavha"><Input value={m.title} onChange={(e) => update(i, { title: e.target.value })} /></Field>
            </div>
            <Field label="Natija (qisqa tavsif)"><Textarea rows={2} value={m.result} onChange={(e) => update(i, { result: e.target.value })} /></Field>
            <Field label="Darslar (har birini yangi qatorga)">
              <Textarea rows={5} value={arrToLines(m.lessons)} onChange={(e) => update(i, { lessons: linesToArr(e.target.value) })} />
            </Field>
            <Field label="Rasm URL"><Input placeholder="https://..." value={m.image} onChange={(e) => update(i, { image: e.target.value })} /></Field>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
