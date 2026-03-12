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
  { id: "funnel", label: "Voronka", icon: "◇" },
  { id: "events", label: "Voqealar", icon: "◎" },
  { id: "users", label: "Userlar", icon: "⊕" },
  { id: "broadcast", label: "Xabarlar", icon: "✦" },
  { id: "courses", label: "Darslar", icon: "▶" },
  { id: "guides", label: "Qo'llanma", icon: "≡" },
  { id: "magnets", label: "Havola", icon: "⊘" },
] as const;

type TabId = (typeof tabs)[number]["id"];

export default function AppLayout() {
  const [activeTab, setActiveTab] = useState<TabId>("home");

  const renderScreen = () => {
    switch (activeTab) {
      case "home": return <DashboardHome />;
      case "funnel": return <FunnelAnalytics />;
      case "events": return <EventTracking />;
      case "users": return <UsersCRM />;
      case "broadcast": return <Broadcast />;
      case "courses": return <CourseManager />;
      case "guides": return <GuidesManager />;
      case "magnets": return <LeadMagnetManager />;
    }
  };

  return (
    <div className="flex h-[100dvh] overflow-hidden">
      {/* Desktop Sidebar — hidden on mobile */}
      <aside className="hidden md:flex flex-col w-56 bg-card border-r border-border/30 flex-shrink-0">
        <div className="flex items-center gap-2 px-5 py-4 border-b border-border/20">
          <span className="text-lg font-bold text-primary">⌂ Admin</span>
          <ThemeToggle />
        </div>
        <nav className="flex-1 overflow-y-auto py-2">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-5 py-2.5 text-sm font-medium transition-all ${isActive
                    ? "bg-primary/10 text-primary border-r-2 border-primary"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                  }`}
              >
                <span className="text-base">{tab.icon}</span>
                {tab.label}
              </button>
            );
          })}
        </nav>
        <div className="px-5 py-3 border-t border-border/20 text-[10px] text-muted-foreground">
          Nuvi Academy Admin v2.0
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header — hidden on desktop */}
        <div className="md:hidden flex items-center justify-between px-4 py-3 border-b border-border/20 flex-shrink-0">
          <span className="text-lg font-bold text-primary">Admin</span>
          <ThemeToggle />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.12 }}
              className="p-3 md:p-6 max-w-6xl mx-auto"
            >
              {renderScreen()}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Mobile Tab Bar — hidden on desktop */}
        <div className="md:hidden flex-shrink-0" style={{
          borderTop: '1px solid rgba(255,255,255,0.08)',
          display: 'flex',
          overflowX: 'auto',
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
                  gap: '2px',
                  padding: '10px 4px 8px',
                  flex: 1,
                  minWidth: '44px',
                  border: 'none',
                  background: isActive ? 'rgba(56,189,248,0.08)' : 'transparent',
                  color: isActive ? 'hsl(199 85% 55%)' : 'hsl(210 10% 50%)',
                  cursor: 'pointer',
                  borderTop: isActive ? '2px solid hsl(199 85% 55%)' : '2px solid transparent',
                  WebkitTapHighlightColor: 'transparent',
                  transition: 'color 0.15s',
                  fontSize: '14px',
                }}
              >
                <span style={{ fontSize: '18px', lineHeight: 1 }}>{tab.icon}</span>
                <span style={{ fontSize: '9px', fontWeight: 500, whiteSpace: 'nowrap', lineHeight: 1 }}>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
