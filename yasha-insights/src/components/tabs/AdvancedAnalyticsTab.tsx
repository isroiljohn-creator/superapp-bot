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

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

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
                    <h3 className="text-sm font-medium mb-4">Daily Active Users (Growth)</h3>
                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={growth?.data || []}>
                                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                                <XAxis dataKey="date" fontSize={12} stroke="#888888" />
                                <YAxis fontSize={12} stroke="#888888" />
                                <Tooltip
                                    contentStyle={{ backgroundColor: 'var(--background)', border: '1px solid var(--border)' }}
                                />
                                <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={2} dot={{ r: 4 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Funnel Chart */}
                <div className="stat-card">
                    <h3 className="text-sm font-medium mb-4">User Funnel (30 Days)</h3>
                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={funnel?.data || []} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} opacity={0.3} />
                                <XAxis type="number" hide />
                                <YAxis dataKey="name" type="category" width={80} fontSize={12} stroke="#888888" />
                                <Tooltip
                                    cursor={{ fill: 'transparent' }}
                                    contentStyle={{ backgroundColor: 'var(--background)', border: '1px solid var(--border)' }}
                                />
                                <Bar dataKey="value" fill="#82ca9d" radius={[0, 4, 4, 0]} label={{ position: 'right', fill: '#888' }} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Retention Chart */}
                <div className="stat-card">
                    <h3 className="text-sm font-medium mb-4">Retention Rates (%)</h3>
                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={retention?.data || []}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                                <XAxis dataKey="name" fontSize={12} stroke="#888888" />
                                <YAxis unit="%" fontSize={12} stroke="#888888" />
                                <Tooltip
                                    cursor={{ fill: 'transparent' }}
                                    contentStyle={{ backgroundColor: 'var(--background)', border: '1px solid var(--border)' }}
                                />
                                <Bar dataKey="value" fill="#ffc658" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Premium Distribution */}
                <div className="stat-card">
                    <h3 className="text-sm font-medium mb-4">Premium vs Free</h3>
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
                                >
                                    {(premium?.data || []).map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ backgroundColor: 'var(--background)', border: '1px solid var(--border)' }}
                                />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}
