import { useState } from 'react';
import {
  LayoutDashboard,
  Users,
  Cpu,
  Star,
  Menu,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { OverviewTab } from './tabs/OverviewTab';
import { RetentionTab } from './tabs/RetentionTab';
import { AICostsTab } from './tabs/AICostsTab';
import { QualityTab } from './tabs/QualityTab';
import { useTelegram } from '@/hooks/useTelegram';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from '@/components/ui/sheet';
import { AdvancedAnalyticsTab } from './tabs/AdvancedAnalyticsTab';

type TabId = 'overview' | 'analytics' | 'retention' | 'ai-costs' | 'quality' | 'referral';

interface Tab {
  id: TabId;
  label: string;
  icon: typeof LayoutDashboard;
}

const tabs: Tab[] = [
  { id: 'overview', label: 'Umumiy', icon: LayoutDashboard },
  { id: 'analytics', label: 'Pro Analitika', icon: BarChart3 },
  { id: 'retention', label: 'Qaytuvchanlik', icon: Users },
  { id: 'ai-costs', label: 'AI Xarajatlari', icon: Cpu },
  { id: 'quality', label: 'Sifat', icon: Star },
];

export function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const { user, hapticFeedback } = useTelegram();
  const [isSheetOpen, setIsSheetOpen] = useState(false);

  const handleTabChange = (tabId: TabId) => {
    hapticFeedback('light');
    setActiveTab(tabId);
    setIsSheetOpen(false);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab />;

      case 'analytics':
        return <AdvancedAnalyticsTab />;
      case 'retention':
        return <RetentionTab />;
      case 'ai-costs':
        return <AICostsTab />;
      case 'quality':
        return <QualityTab />;
      default:
        return <OverviewTab />;
    }
  };

  return (
    <div className="min-h-screen bg-background selection:bg-primary/20">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-panel backdrop-blur-2xl border-b border-white/5">
        <div className="container mx-auto flex items-center justify-between px-4 h-16">
          <div className="flex items-center gap-4">
            <Sheet open={isSheetOpen} onOpenChange={setIsSheetOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden hover:bg-primary/10 transition-transform active:scale-90">
                  <Menu className="h-6 w-6 text-primary" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-80 p-0 glass-panel border-r border-white/5">
                <div className="p-8 border-b border-white/5">
                  <h1 className="text-3xl font-black tracking-tighter text-gradient-vibrant">
                    YASHA <span className="text-foreground">Admin</span>
                  </h1>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="px-2 py-0.5 rounded-full bg-primary/10 text-[10px] font-bold text-primary border border-primary/20 uppercase tracking-widest animate-pulse">
                      v2.7 Refresh Fix
                    </span>
                  </div>
                </div>
                <nav className="p-4 space-y-2">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => handleTabChange(tab.id)}
                      className={cn(
                        'w-full flex items-center gap-4 px-6 py-4 rounded-2xl text-sm font-bold transition-all duration-300',
                        activeTab === tab.id
                          ? 'bg-primary text-white shadow-lg shadow-primary/25 glow-primary scale-[1.02]'
                          : 'text-muted-foreground hover:bg-white/5 hover:text-foreground hover:translate-x-1'
                      )}
                    >
                      <tab.icon className={cn("h-5 w-5", activeTab === tab.id ? "animate-pulse" : "")} />
                      {tab.label}
                    </button>
                  ))}
                </nav>
              </SheetContent>
            </Sheet>

            <div className="flex flex-col">
              <h1 className="text-xl font-bold tracking-tight text-gradient-vibrant">YASHA</h1>
              <p className="text-[10px] text-muted-foreground uppercase tracking-[0.2em] font-black -mt-1 opacity-60">Admin Portal</p>
            </div>

            {/* Desktop Tab Bar */}
            <nav className="hidden md:flex items-center gap-1 ml-8 h-10 p-1 bg-secondary/50 rounded-xl border border-white/5">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={cn(
                    'flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all duration-300',
                    activeTab === tab.id
                      ? 'bg-primary text-white shadow-md glow-primary'
                      : 'text-muted-foreground hover:bg-white/5 hover:text-foreground'
                  )}
                >
                  <tab.icon className="h-3.5 w-3.5" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <ThemeToggle />
            {user && (
              <div className="flex items-center gap-3 pl-4 border-l border-white/10">
                <div className="hidden sm:flex flex-col items-end">
                  <span className="text-xs font-bold text-foreground leading-none">{user.first_name}</span>
                  <span className="text-[9px] text-muted-foreground uppercase font-black tracking-widest leading-none mt-1">Superadmin</span>
                </div>
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-primary to-info p-[1px] shadow-lg shadow-primary/20">
                  <div className="w-full h-full rounded-[14px] bg-background flex items-center justify-center">
                    <span className="text-sm font-black text-primary">
                      {user.first_name[0]}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-4 pb-24 md:pb-8">
        <div className="max-w-6xl mx-auto">{renderTabContent()}</div>
      </main>

      {/* Bottom Tab Bar - Mobile */}
      <nav className="fixed bottom-0 left-0 right-0 md:hidden bg-background/80 backdrop-blur-xl border-t border-border z-50">
        <div className="flex items-center justify-around h-16">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={cn(
                'flex flex-col items-center gap-1 py-2 px-4 transition-colors',
                activeTab === tab.id
                  ? 'text-primary'
                  : 'text-muted-foreground'
              )}
            >
              <tab.icon
                className={cn(
                  'h-5 w-5 transition-transform',
                  activeTab === tab.id && 'scale-110'
                )}
              />
              <span className="text-[10px] font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
}

export default AdminDashboard;
