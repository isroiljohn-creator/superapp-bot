import {
    LineChart,
    Line,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from 'recharts';
import { useGrowth, useFunnel, useRetentionGraph, usePremiumDist } from '@/hooks/useAnalytics';
import { Loader2 } from 'lucide-react';

const COLORS = [
    'hsl(var(--chart-1))',
    'hsl(var(--chart-2))',
    'hsl(var(--chart-3))',
    'hsl(var(--chart-4))'
];

export function AdvancedAnalyticsTab() {
    const { data: growth, isLoading: l1 } = useGrowth();
    const { data: funnel, isLoading: l2 } = useFunnel();
    const { data: retention, isLoading: l3 } = useRetentionGraph();
    const { data: premium, isLoading: l4 } = usePremiumDist();

    const isLoading = l1 || l2 || l3 || l4;

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-12">
            <div className="px-2">
                <h2 className="text-2xl font-black tracking-tight text-foreground/90">Kengaytirilgan Analitika</h2>
                <p className="text-sm text-muted-foreground font-medium mt-1">O'sish, konversiya va qaytuvchanlik ko'rsatkichlari bo'yicha chuqur tahlil.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Growth Chart */}
                <div className="glass-card">
                    <h3 className="stat-label mb-6">Kunlik Faol Foydalanuvchilar (DAU)</h3>
                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={growth?.data || []}>
                                <CartesianGrid strokeDasharray="3 3" opacity={0.05} vertical={false} stroke="hsl(var(--foreground))" />
                                <XAxis
                                    dataKey="date"
                                    fontSize={10}
                                    tickLine={false}
                                    axisLine={false}
                                    stroke="hsl(var(--muted-foreground))"
                                    tick={{ fill: 'hsl(var(--muted-foreground))', fontWeight: 'bold' }}
                                    dy={10}
                                />
                                <YAxis
                                    fontSize={10}
                                    tickLine={false}
                                    axisLine={false}
                                    stroke="hsl(var(--muted-foreground))"
                                    tick={{ fill: 'hsl(var(--muted-foreground))', fontWeight: 'bold' }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'hsl(var(--card)/0.8)',
                                        backdropFilter: 'blur(12px)',
                                        borderColor: 'hsl(var(--white)/0.1)',
                                        color: 'hsl(var(--foreground))',
                                        borderRadius: '16px',
                                        fontSize: '11px',
                                        fontWeight: 'bold',
                                        border: '1px solid hsla(0,0%,100%,0.1)',
                                        boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'
                                    }}
                                    itemStyle={{ color: 'hsl(var(--primary))' }}
                                    cursor={{ stroke: 'hsl(var(--primary))', strokeWidth: 2, strokeDasharray: '3 3' }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="value"
                                    stroke="hsl(var(--primary))"
                                    strokeWidth={3}
                                    dot={{ r: 4, fill: "hsl(var(--background))", strokeWidth: 2, stroke: "hsl(var(--primary))" }}
                                    activeDot={{ r: 6, fill: "hsl(var(--primary))", strokeWidth: 0 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Funnel Chart */}
                <div className="glass-card">
                    <h3 className="stat-label mb-6">Foydalanuvchi Voronkasi (30 kun)</h3>
                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={funnel?.data || []} layout="vertical" barSize={32}>
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} opacity={0.05} stroke="hsl(var(--foreground))" />
                                <XAxis type="number" hide />
                                <YAxis
                                    dataKey="name"
                                    type="category"
                                    width={100}
                                    fontSize={10}
                                    tickLine={false}
                                    axisLine={false}
                                    stroke="hsl(var(--muted-foreground))"
                                    tick={{ fill: 'hsl(var(--muted-foreground))', fontWeight: 'bold' }}
                                />
                                <Tooltip
                                    cursor={{ fill: 'hsl(var(--muted)/0.1)', radius: 8 }}
                                    contentStyle={{
                                        backgroundColor: 'hsl(var(--card)/0.8)',
                                        backdropFilter: 'blur(12px)',
                                        borderColor: 'hsl(var(--white)/0.1)',
                                        borderRadius: '16px',
                                        fontSize: '11px',
                                        fontWeight: 'bold'
                                    }}
                                />
                                <Bar
                                    dataKey="value"
                                    fill="hsl(var(--chart-2))"
                                    radius={[0, 8, 8, 0]}
                                    label={{ position: 'right', fill: 'hsl(var(--foreground))', fontSize: 10, fontWeight: 'bold' }}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Retention Chart */}
                <div className="glass-card">
                    <h3 className="stat-label mb-6">Qaytuvchanlik darajasi (%)</h3>
                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={retention?.data || []}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.05} stroke="hsl(var(--foreground))" />
                                <XAxis
                                    dataKey="name"
                                    fontSize={10}
                                    tickLine={false}
                                    axisLine={false}
                                    stroke="hsl(var(--muted-foreground))"
                                    tick={{ fill: 'hsl(var(--muted-foreground))', fontWeight: 'bold' }}
                                    dy={10}
                                />
                                <YAxis
                                    unit="%"
                                    fontSize={10}
                                    tickLine={false}
                                    axisLine={false}
                                    stroke="hsl(var(--muted-foreground))"
                                    tick={{ fill: 'hsl(var(--muted-foreground))', fontWeight: 'bold' }}
                                />
                                <Tooltip
                                    cursor={{ fill: 'hsl(var(--muted)/0.1)', radius: 8 }}
                                    contentStyle={{
                                        backgroundColor: 'hsl(var(--card)/0.8)',
                                        backdropFilter: 'blur(12px)',
                                        borderColor: 'hsl(var(--white)/0.1)',
                                        borderRadius: '16px',
                                        fontSize: '11px',
                                        fontWeight: 'bold'
                                    }}
                                />
                                <Bar dataKey="value" fill="hsl(var(--chart-3))" radius={[8, 8, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Premium Distribution */}
                <div className="glass-card">
                    <h3 className="stat-label mb-6">Premium vs Bepul</h3>
                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={premium?.data || []}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={90}
                                    paddingAngle={8}
                                    dataKey="value"
                                    stroke="hsl(var(--card))"
                                    strokeWidth={4}
                                >
                                    {(premium?.data || []).map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'hsl(var(--card)/0.8)',
                                        backdropFilter: 'blur(12px)',
                                        borderColor: 'hsl(var(--white)/0.1)',
                                        borderRadius: '16px',
                                        fontSize: '11px',
                                        fontWeight: 'bold'
                                    }}
                                />
                                <Legend wrapperStyle={{ fontSize: '10px', fontWeight: 'bold', paddingTop: '20px' }} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}
