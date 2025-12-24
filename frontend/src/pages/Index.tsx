import React, { useState } from 'react';
import { Onboarding } from '@/components/Onboarding';
import { BottomNavigation } from '@/components/BottomNavigation';
import { HomeScreen } from '@/screens/HomeScreen';
import { MenuScreen } from '@/screens/MenuScreen';
import { WorkoutScreen } from '@/screens/WorkoutScreen';
import { HabitsScreen } from '@/screens/HabitsScreen';
import { ProfileScreen } from '@/screens/ProfileScreen';
import { UserProvider, useUser } from '@/contexts/UserContext';

const AppContent: React.FC = () => {
  const { isOnboarded, isLoading } = useUser();
  const [activeTab, setActiveTab] = useState('home');

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!isOnboarded) {
    return <Onboarding />;
  }

  const renderScreen = () => {
    switch (activeTab) {
      case 'home': return <HomeScreen />;
      case 'menu': return <MenuScreen />;
      case 'workout': return <WorkoutScreen />;
      case 'habits': return <HabitsScreen />;
      case 'profile': return <ProfileScreen />;
      default: return <HomeScreen />;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {renderScreen()}
      <BottomNavigation activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
};

const Index: React.FC = () => {
  return (
    <UserProvider>
      <AppContent />
    </UserProvider>
  );
};

export default Index;
