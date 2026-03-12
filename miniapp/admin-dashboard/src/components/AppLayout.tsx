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

const allTabs = [
  { id: "home", label: "Asosiy", icon: "⌂" },
  { id: "users", label: "Userlar", icon: "⊕" },
  { id: "funnel", label: "Voronka", icon: "◇" },
  { id: "broadcast", label: "Xabarlar", icon: "✦" },
  { id: "courses", label: "Darslar", icon: "▶" },
  { id: "events", label: "Voqealar", icon: "◎" },
  { id: "guides", label: "Qo'llanma", icon: "≡" },
  { id: "magnets", label: "Havola", icon: "⊘" },
] as const;

// Mobile: 5 main tabs shown in bottom bar
const mobileTabs = allTabs.slice(0, 5);
const moreTabs = allTabs.slice(5);

type TabId = (typeof allTabs)[number]["id"];

export default function AppLayout() {
  const [activeTab, setActiveTab] = useState<TabId>("home");
  const [showMore, setShowMore] = useState(false);

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

  const isInMore = moreTabs.some(t => t.id === activeTab);

  return (
    <div className="flex h-[100dvh] overflow-hidden">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-52 bg-card border-r border-border/30 flex-shrink-0">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border/20">
          <span className="text-base font-bold text-primary">⌂ Admin</span>
          <div className="ml-auto"><ThemeToggle /></div>
        </div>
        <nav className="flex-1 overflow-y-auto py-1">
          {allTabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => { setActiveTab(tab.id); setShowMore(false); }}
                className={`w-full flex items-center gap-2.5 px-4 py-2 text-[13px] font-medium transition-all ${isActive
                    ? "bg-primary/10 text-primary border-r-2 border-primary"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                  }`}
              >
                <span className="text-sm">{tab.icon}</span>
                {tab.label}
              </button>
            );
          })}
        </nav>
        <div className="px-4 py-2 border-t border-border/20 text-[9px] text-muted-foreground">
          Admin Panel v2.0
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header */}
        <div className="md:hidden flex items-center justify-between px-3 py-2.5 border-b border-border/20 flex-shrink-0">
          <span className="text-base font-bold text-primary">Admin</span>
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
              className="p-3 md:p-5 max-w-5xl mx-auto"
            >
              {renderScreen()}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* More menu overlay */}
        <AnimatePresence>
          {showMore && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="md:hidden fixed inset-0 z-40 bg-black/50"
              onClick={() => setShowMore(false)}
            >
              <motion.div
                initial={{ y: 100 }}
                animate={{ y: 0 }}
                exit={{ y: 100 }}
                className="absolute bottom-16 left-3 right-3 bg-card rounded-xl border border-border/30 p-2 shadow-lg"
                onClick={(e) => e.stopPropagation()}
              >
                {moreTabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => { setActiveTab(tab.id); setShowMore(false); }}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium ${activeTab === tab.id ? "bg-primary/10 text-primary" : "text-foreground"
                      }`}
                  >
                    <span>{tab.icon}</span>
                    {tab.label}
                  </button>
                ))}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Mobile Tab Bar — only 5 tabs + More */}
        <div className="md:hidden flex-shrink-0" style={{
          borderTop: '1px solid rgba(255,255,255,0.08)',
          display: 'flex',
          background: 'hsl(220 20% 7%)',
          paddingBottom: 'env(safe-area-inset-bottom, 0px)',
        }}>
          {mobileTabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => { setActiveTab(tab.id); setShowMore(false); }}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '1px',
                  padding: '6px 2px 5px',
                  flex: 1,
                  border: 'none',
                  background: isActive ? 'rgba(56,189,248,0.08)' : 'transparent',
                  color: isActive ? 'hsl(199 85% 55%)' : 'hsl(210 10% 50%)',
                  cursor: 'pointer',
                  borderTop: isActive ? '2px solid hsl(199 85% 55%)' : '2px solid transparent',
                  WebkitTapHighlightColor: 'transparent',
                  transition: 'color 0.15s',
                }}
              >
                <span style={{ fontSize: '16px', lineHeight: 1 }}>{tab.icon}</span>
                <span style={{ fontSize: '9px', fontWeight: 500, lineHeight: 1 }}>{tab.label}</span>
              </button>
            );
          })}
          {/* More button */}
          <button
            onClick={() => setShowMore(!showMore)}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '1px',
              padding: '6px 2px 5px',
              flex: 1,
              border: 'none',
              background: (isInMore || showMore) ? 'rgba(56,189,248,0.08)' : 'transparent',
              color: (isInMore || showMore) ? 'hsl(199 85% 55%)' : 'hsl(210 10% 50%)',
              cursor: 'pointer',
              borderTop: isInMore ? '2px solid hsl(199 85% 55%)' : '2px solid transparent',
              WebkitTapHighlightColor: 'transparent',
              transition: 'color 0.15s',
            }}
          >
            <span style={{ fontSize: '16px', lineHeight: 1 }}>⋯</span>
            <span style={{ fontSize: '9px', fontWeight: 500, lineHeight: 1 }}>Yana</span>
          </button>
        </div>
      </div>
    </div>
  );
}
