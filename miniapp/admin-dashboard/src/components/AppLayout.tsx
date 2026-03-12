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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100dvh', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.08)', flexShrink: 0 }}>
        <span style={{ fontSize: '18px', fontWeight: 700, color: 'hsl(199 85% 55%)' }}>Admin</span>
        <ThemeToggle />
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', minHeight: 0 }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15 }}
            style={{ padding: '12px' }}
          >
            {renderScreen()}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Tab Bar — all inline styles, no external deps */}
      <div style={{
        flexShrink: 0,
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
  );
}
