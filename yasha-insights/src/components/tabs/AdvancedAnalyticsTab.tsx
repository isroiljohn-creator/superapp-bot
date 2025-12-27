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
        <div className="space-y-6 animate-fade-in pb-12">
            <div>
                <h2 className="text-xl font-semibold">Advanced Analytics</h2>
                <p className="text-sm text-muted-foreground">Deep dive into growth, conversion, and retention metrics.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Growth Chart */}
                <div className="stat-card">
                    <h3 className="text-sm font-medium mb-4 text-muted-foreground uppercase tracking-wider">Daily Active Users</h3>
                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={growth?.data || []}>
                                <CartesianGrid strokeDasharray="3 3" opacity={0.1} vertical={false} stroke="hsl(var(--muted-foreground))" />
                                <XAxis
                                    dataKey="date"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                    stroke="hsl(var(--muted-foreground))"
                                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                                    dy={10}
                                />
                                <YAxis
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                    stroke="hsl(var(--muted-foreground))"
                                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'hsl(var(--card))',
                                        borderColor: 'hsl(var(--border))',
                                        color: 'hsl(var(--foreground))',
                                        borderRadius: 'var(--radius)',
                                        fontSize: '12px'
                                    }}
                                    itemStyle={{ color: 'hsl(var(--foreground))' }}
                                    cursor={{ stroke: 'hsl(var(--muted-foreground))', strokeWidth: 1, opacity: 0.5 }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="value"
                                    stroke="hsl(var(--chart-1))"
                                    strokeWidth={2}
                                    dot={{ r: 4, fill: "hsl(var(--background))", strokeWidth: 2 }}
                                    activeDot={{ r: 6, fill: "hsl(var(--chart-1))" }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Funnel Chart */}
                <div className="stat-card">
                    <h3 className="text-sm font-medium mb-4 text-muted-foreground uppercase tracking-wider">User Funnel (30 Days)</h3>
                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={funnel?.data || []} layout="vertical" barSize={32}>
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} opacity={0.1} stroke="hsl(var(--muted-foreground))" />
                                <XAxis type="number" hide />
                                <YAxis
                                    dataKey="name"
                                    type="category"
                                    width={80}
                                    fontSize={11}
                                    tickLine={false}
                                    axisLine={false}
                                    stroke="hsl(var(--muted-foreground))"
                                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                                />
                                <Tooltip
                                    cursor={{ fill: 'hsl(var(--muted)/0.2)' }}
                                    contentStyle={{
                                        backgroundColor: 'hsl(var(--card))',
                                        borderColor: 'hsl(var(--border))',
                                        color: 'hsl(var(--foreground))',
                                        borderRadius: 'var(--radius)',
                                        fontSize: '12px'
                                    }}
                                />
                                <Bar
                                    dataKey="value"
                                    fill="hsl(var(--chart-2))"
                                    radius={[0, 4, 4, 0]}
                                    label={{ position: 'right', fill: 'hsl(var(--foreground))', fontSize: 12 }}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Retention Chart */}
                <div className="stat-card">
                    <h3 className="text-sm font-medium mb-4 text-muted-foreground uppercase tracking-wider">Retention Rates (%)</h3>
                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={retention?.data || []}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.1} stroke="hsl(var(--muted-foreground))" />
                                <XAxis
                                    dataKey="name"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                    stroke="hsl(var(--muted-foreground))"
                                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                                    dy={10}
                                />
                                <YAxis
                                    unit="%"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                    stroke="hsl(var(--muted-foreground))"
                                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                                />
                                <Tooltip
                                    cursor={{ fill: 'hsl(var(--muted)/0.2)' }}
                                    contentStyle={{
                                        backgroundColor: 'hsl(var(--card))',
                                        borderColor: 'hsl(var(--border))',
                                        color: 'hsl(var(--foreground))',
                                        borderRadius: 'var(--radius)',
                                        fontSize: '12px'
                                    }}
                                />
                                <Bar dataKey="value" fill="hsl(var(--chart-3))" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Premium Distribution */}
                <div className="stat-card">
                    <h3 className="text-sm font-medium mb-4 text-muted-foreground uppercase tracking-wider">Premium vs Free</h3>
                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={premium?.data || []}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                    stroke="hsl(var(--card))"
                                    strokeWidth={2}
                                >
                                    {(premium?.data || []).map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'hsl(var(--card))',
                                        borderColor: 'hsl(var(--border))',
                                        color: 'hsl(var(--foreground))',
                                        borderRadius: 'var(--radius)',
                                        fontSize: '12px'
                                    }}
                                    itemStyle={{ color: 'hsl(var(--foreground))' }}
                                />
                                <Legend wrapperStyle={{ fontSize: '12px', color: 'hsl(var(--muted-foreground))' }} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}
