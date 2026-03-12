import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ThemeToggle } from "./ThemeToggle";
import DashboardHome from "@/pages/DashboardHome";
import FunnelAnalytics from "@/pages/FunnelAnalytics";
import EventTracking from "@/pages/EventTracking";
import UsersCRM from "@/pages/UsersCRM";
import Broadcast from "@/pages/Broadcast";
import CourseManager from "@/pages/CourseManager";
import GuidesManager from "@/pages/GuidesManager";
import LeadMagnetManager from "@/pages/LeadMagnetManager";

const tabs = [
  { id: "home", label: "Asosiy", icon: "⌂" },
  { id: "users", label: "Userlar", icon: "⊕" },
  { id: "analytics", label: "Tahlil", icon: "◇" },
  { id: "broadcast", label: "Xabarlar", icon: "✦" },
  { id: "material", label: "Material", icon: "▶" },
] as const;

type TabId = (typeof tabs)[number]["id"];

// Sub-tabs for Analytics
const analyticsSubTabs = [
  { id: "funnel", label: "Voronka" },
  { id: "events", label: "Voqealar" },
] as const;
type AnalyticsSubTab = (typeof analyticsSubTabs)[number]["id"];

// Sub-tabs for Material
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

  const renderScreen = () => {
    switch (activeTab) {
      case "home": return <DashboardHome />;
      case "users": return <UsersCRM />;
      case "analytics":
        return (
          <div className="space-y-2">
            <SubTabBar tabs={analyticsSubTabs} active={analyticsTab} onChange={(id) => setAnalyticsTab(id as AnalyticsSubTab)} />
            {analyticsTab === "funnel" ? <FunnelAnalytics /> : <EventTracking />}
          </div>
        );
      case "broadcast": return <Broadcast />;
      case "material":
        return (
          <div className="space-y-2">
            <SubTabBar tabs={materialSubTabs} active={materialTab} onChange={(id) => setMaterialTab(id as MaterialSubTab)} />
            {materialTab === "courses" ? <CourseManager /> :
              materialTab === "guides" ? <GuidesManager /> : <LeadMagnetManager />}
          </div>
        );
    }
  };

  return (
    <div className="flex h-[100dvh] overflow-hidden">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-48 bg-card border-r border-border/30 flex-shrink-0">
        <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border/20">
          <span className="text-sm font-bold text-primary">⌂ Admin</span>
          <div className="ml-auto"><ThemeToggle /></div>
        </div>
        <nav className="flex-1 overflow-y-auto py-1">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-2 px-3 py-2 text-[12px] font-medium transition-all ${isActive
                  ? "bg-primary/10 text-primary border-r-2 border-primary"
                  : "text-muted-foreground hover:bg-secondary"
                  }`}
              >
                <span className="text-sm">{tab.icon}</span>
                {tab.label}
              </button>
            );
          })}
        </nav>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header */}
        <div className="md:hidden flex items-center justify-between px-3 py-2 border-b border-border/20 flex-shrink-0">
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
              className="p-2.5 md:p-5 max-w-5xl mx-auto"
            >
              {renderScreen()}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Mobile Tab Bar */}
        <div className="md:hidden flex-shrink-0" style={{
          borderTop: '1px solid rgba(255,255,255,0.1)',
          display: 'flex',
          background: 'hsl(220 20% 7%)',
          paddingBottom: 'env(safe-area-inset-bottom, 0px)',
        }}>
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '1px',
                  padding: '7px 2px 5px',
                  flex: 1,
                  border: 'none',
                  background: isActive ? 'rgba(56,189,248,0.1)' : 'transparent',
                  color: isActive ? 'hsl(199 85% 55%)' : 'hsl(210 10% 45%)',
                  cursor: 'pointer',
                  borderTop: isActive ? '2px solid hsl(199 85% 55%)' : '2px solid transparent',
                  WebkitTapHighlightColor: 'transparent',
                  transition: 'color 0.15s',
                }}
              >
                <span style={{ fontSize: '15px', lineHeight: 1 }}>{tab.icon}</span>
                <span style={{ fontSize: '9px', fontWeight: 500, lineHeight: 1 }}>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// Reusable sub-tab component
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
          className={`flex-1 py-1.5 rounded-md text-[11px] font-medium text-center transition-all ${active === tab.id
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
