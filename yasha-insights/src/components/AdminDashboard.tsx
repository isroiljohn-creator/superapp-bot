import { useState } from 'react';
import {
  LayoutDashboard,
  Users,
  Cpu,
  Star,
  Menu,
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

type TabId = 'overview' | 'retention' | 'ai-costs' | 'quality';

interface Tab {
  id: TabId;
  label: string;
  icon: typeof LayoutDashboard;
}

const tabs: Tab[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'retention', label: 'Retention', icon: Users },
  { id: 'ai-costs', label: 'AI Costs', icon: Cpu },
  { id: 'quality', label: 'Quality', icon: Star },
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
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border">
        <div className="flex items-center justify-between px-4 h-14">
          <div className="flex items-center gap-3">
            <Sheet open={isSheetOpen} onOpenChange={setIsSheetOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-64 p-0">
                <div className="p-4 border-b border-border">
                  <h2 className="font-semibold text-lg">YASHA Admin</h2>
                  <p className="text-xs text-muted-foreground">Analytics Dashboard</p>
                </div>
                <nav className="p-2">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => handleTabChange(tab.id)}
                      className={cn(
                        'w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors',
                        activeTab === tab.id
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                      )}
                    >
                      <tab.icon className="h-4 w-4" />
                      {tab.label}
                    </button>
                  ))}
                </nav>
              </SheetContent>
            </Sheet>
            <div>
              <h1 className="font-semibold text-sm">YASHA</h1>
              <p className="text-[10px] text-muted-foreground">Admin Analytics</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            {user && (
              <div className="flex items-center gap-2 pl-2 border-l border-border">
                <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center">
                  <span className="text-xs font-medium text-primary">
                    {user.first_name[0]}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Tab Bar - Desktop */}
        <nav className="hidden md:flex items-center gap-1 px-4 pb-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
                activeTab === tab.id
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
              )}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      {/* Main Content */}
      <main className="p-4 pb-24 md:pb-8">
        <div className="max-w-4xl mx-auto">{renderTabContent()}</div>
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
