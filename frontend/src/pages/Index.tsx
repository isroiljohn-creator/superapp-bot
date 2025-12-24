import React, { useState, useEffect } from 'react';
import { Onboarding } from '@/components/Onboarding';
import { BottomNavigation } from '@/components/BottomNavigation';
import { SplashScreen } from '@/components/SplashScreen';
import { HomeScreen } from '@/screens/HomeScreen';
import { MenuScreen } from '@/screens/MenuScreen';
import { WorkoutScreen } from '@/screens/WorkoutScreen';
import { HabitsScreen } from '@/screens/HabitsScreen';
import { ProfileScreen } from '@/screens/ProfileScreen';
import { AiCoachScreen } from '@/screens/AiCoachScreen';
import { WeightScreen } from '@/screens/WeightScreen';
import { AchievementsScreen } from '@/screens/AchievementsScreen';
import { MeditationScreen } from '@/screens/MeditationScreen';
import { RecipesScreen } from '@/screens/RecipesScreen';
import { ReportsScreen } from '@/screens/ReportsScreen';
import { FriendsScreen } from '@/screens/FriendsScreen';
import { ChallengesScreen } from '@/screens/ChallengesScreen';
import { CaloriesScreen } from '@/screens/CaloriesScreen';
import { WorkoutLibraryScreen } from '@/screens/WorkoutLibraryScreen';
import { DailyTasksScreen } from '@/screens/DailyTasksScreen';
import { ShopScreen } from '@/screens/ShopScreen';
import { NotificationSettingsScreen } from '@/screens/NotificationSettingsScreen';
import { ExploreScreen } from '@/screens/ExploreScreen';
import { SettingsScreen } from '@/screens/SettingsScreen';
import { UserProvider, useUser } from '@/contexts/UserContext';
import { LanguageProvider } from '@/contexts/LanguageContext';

const AppContent: React.FC = () => {
  const { isOnboarded } = useUser();
  const [activeTab, setActiveTab] = useState('home');
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    // Splash faqat bir marta ko'rsatiladi
    const hasSeenSplash = sessionStorage.getItem('yasha_splash_seen');
    if (hasSeenSplash) {
      setShowSplash(false);
    }
  }, []);

  const handleSplashComplete = () => {
    sessionStorage.setItem('yasha_splash_seen', 'true');
    setShowSplash(false);
  };

  if (showSplash) {
    return <SplashScreen onComplete={handleSplashComplete} />;
  }

  if (!isOnboarded) {
    return <Onboarding />;
  }

  const renderScreen = () => {
    switch (activeTab) {
      case 'home': return <HomeScreen onNavigate={setActiveTab} />;
      case 'menu': return <MenuScreen />;
      case 'workout': return <WorkoutScreen />;
      case 'habits': return <HabitsScreen />;
      case 'profile': return <ProfileScreen onNavigate={setActiveTab} />;
      case 'ai-coach': return <AiCoachScreen />;
      case 'weight': return <WeightScreen onBack={() => setActiveTab('explore')} />;
      case 'achievements': return <AchievementsScreen onBack={() => setActiveTab('explore')} />;
      case 'meditation': return <MeditationScreen onBack={() => setActiveTab('explore')} />;
      case 'recipes': return <RecipesScreen />;
      case 'reports': return <ReportsScreen onBack={() => setActiveTab('explore')} />;
      case 'friends': return <FriendsScreen onBack={() => setActiveTab('explore')} />;
      case 'challenges': return <ChallengesScreen onBack={() => setActiveTab('explore')} />;
      case 'calories': return <CaloriesScreen onBack={() => setActiveTab('explore')} />;
      case 'workout-library': return <WorkoutLibraryScreen onBack={() => setActiveTab('explore')} />;
      case 'daily-tasks': return <DailyTasksScreen onBack={() => setActiveTab('explore')} />;
      case 'shop': return <ShopScreen onBack={() => setActiveTab('explore')} />;
      case 'notifications': return <NotificationSettingsScreen onBack={() => setActiveTab('profile')} />;
      case 'explore': return <ExploreScreen onNavigate={setActiveTab} onBack={() => setActiveTab('home')} />;
      case 'settings': return <SettingsScreen onBack={() => setActiveTab('profile')} />;
      default: return <HomeScreen onNavigate={setActiveTab} />;
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
    <LanguageProvider>
      <UserProvider>
        <AppContent />
      </UserProvider>
    </LanguageProvider>
  );
};

export default Index;
