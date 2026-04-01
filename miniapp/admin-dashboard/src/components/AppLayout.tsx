import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Home, Users, BarChart3, Send, FolderOpen, Settings as SettingsIcon, Briefcase } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";
import DashboardHome from "@/pages/DashboardHome";
import FunnelAnalytics from "@/pages/FunnelAnalytics";
import EventTracking from "@/pages/EventTracking";
import UsersCRM from "@/pages/UsersCRM";
import Broadcast from "@/pages/Broadcast";
import CourseManager from "@/pages/CourseManager";
import GuidesManager from "@/pages/GuidesManager";
import LeadMagnetManager from "@/pages/LeadMagnetManager";
import Settings from "@/pages/Settings";
import JobsManager from "@/pages/JobsManager";
import ABTests from "@/pages/ABTests";
import ScheduledMessages from "@/pages/ScheduledMessages";
import PromptManager from "@/pages/PromptManager";

const tabs = [
  { id: "home", label: "Asosiy", icon: Home },
  { id: "users", label: "Userlar", icon: Users },
  { id: "analytics", label: "Tahlil", icon: BarChart3 },
  { id: "broadcast", label: "Xabarlar", icon: Send },
  { id: "material", label: "Material", icon: FolderOpen },
  { id: "jobs", label: "Vakansiya", icon: Briefcase },
  { id: "settings", label: "Sozlama", icon: SettingsIcon },
] as const;

type TabId = (typeof tabs)[number]["id"];

const analyticsSubTabs = [
  { id: "funnel", label: "Voronka" },
  { id: "events", label: "Voqealar" },
  { id: "abtests", label: "A/B Test" },
] as const;
type AnalyticsSubTab = (typeof analyticsSubTabs)[number]["id"];

const materialSubTabs = [
  { id: "courses", label: "Darslar" },
  { id: "guides", label: "Qo'llanma" },
  { id: "magnets", label: "Havolalar" },
] as const;
type MaterialSubTab = (typeof materialSubTabs)[number]["id"];

export default function AppLayout() {
  const [activeTab, setActiveTab] = useState<TabId>("home");
  const [analyticsTab, setAnalyticsTab] = useState<AnalyticsSubTab>("funnel");
  const [materialTab, setMaterialTab] = useState<MaterialSubTab>("courses");
  const [broadcastTab, setBroadcastTab] = useState<"broadcast" | "scheduled">("broadcast");
  const [settingsTab, setSettingsTab] = useState<"settings" | "prompts">("settings");

  const renderScreen = () => {
    switch (activeTab) {
      case "home": return <DashboardHome />;
      case "users": return <UsersCRM />;
      case "analytics":
        return (
          <div className="space-y-3">
            <SubTabBar tabs={analyticsSubTabs} active={analyticsTab} onChange={(id) => setAnalyticsTab(id as AnalyticsSubTab)} />
            {analyticsTab === "funnel" ? <FunnelAnalytics /> :
              analyticsTab === "events" ? <EventTracking /> : <ABTests />}
          </div>
        );
      case "broadcast":
        return (
          <div className="space-y-3">
            <SubTabBar tabs={[{ id: "broadcast", label: "Xabar" }, { id: "scheduled", label: "Rejali" }] as const} active={broadcastTab} onChange={(id) => setBroadcastTab(id as any)} />
            {broadcastTab === "broadcast" ? <Broadcast /> : <ScheduledMessages />}
          </div>
        );
      case "material":
        return (
          <div className="space-y-3">
            <SubTabBar tabs={materialSubTabs} active={materialTab} onChange={(id) => setMaterialTab(id as MaterialSubTab)} />
            {materialTab === "courses" ? <CourseManager /> :
              materialTab === "guides" ? <GuidesManager /> : <LeadMagnetManager />}
          </div>
        );
      case "jobs":
        return <JobsManager />;
      case "settings":
        return (
          <div className="space-y-3">
            <SubTabBar tabs={[{ id: "settings", label: "Sozlama" }, { id: "prompts", label: "Promtlar" }] as const} active={settingsTab} onChange={(id) => setSettingsTab(id as any)} />
            {settingsTab === "settings" ? <Settings /> : <PromptManager />}
          </div>
        );
    }
  };

  return (
    <div className="flex h-[100dvh] overflow-hidden">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-48 bg-card border-r border-border/30 flex-shrink-0">
        <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border/20">
          <span className="text-sm font-bold text-primary">Admin Panel</span>
          <div className="ml-auto"><ThemeToggle /></div>
        </div>
        <nav className="flex-1 overflow-y-auto py-1">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium transition-all ${isActive
                  ? "bg-primary/10 text-primary border-r-2 border-primary"
                  : "text-muted-foreground hover:bg-secondary"
                  }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header */}
        <div className="md:hidden flex items-center justify-between px-3 py-2.5 border-b border-border/20 flex-shrink-0">
          <span className="text-sm font-bold text-primary">Admin Panel</span>
          <ThemeToggle />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 3 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.1 }}
              className="p-3 md:p-5 max-w-5xl mx-auto"
            >
              {renderScreen()}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Mobile Tab Bar */}
        <div className="md:hidden flex-shrink-0 flex border-t border-border/20 bg-card">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-2.5 transition-colors ${isActive ? "text-primary" : "text-muted-foreground"
                  }`}
                style={{
                  borderTop: isActive ? '2px solid hsl(199 85% 55%)' : '2px solid transparent',
                  background: isActive ? 'rgba(56,189,248,0.06)' : 'transparent',
                  WebkitTapHighlightColor: 'transparent',
                }}
              >
                <Icon className="h-5 w-5" strokeWidth={isActive ? 2.2 : 1.5} />
                <span className="text-[10px] font-medium leading-none">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function SubTabBar({ tabs, active, onChange }: {
  tabs: readonly { id: string; label: string }[];
  active: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="flex gap-0.5 p-0.5 bg-secondary/60 rounded-lg">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`flex-1 py-2 rounded-md text-xs font-medium text-center transition-all ${active === tab.id
            ? "bg-card shadow-sm text-foreground"
            : "text-muted-foreground hover:text-foreground"
            }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
