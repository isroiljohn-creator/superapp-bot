import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, UserPlus, Trophy, Swords, ArrowLeft, Search, Crown, Medal, Award } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useLanguage } from '@/contexts/LanguageContext';
import { useUser } from '@/contexts/UserContext';
import { useToast } from '@/hooks/use-toast';

interface Friend {
  id: string;
  name: string;
  avatar?: string;
  level: number;
  xp: number;
  status: 'online' | 'offline';
}

interface LeaderboardEntry {
  rank: number;
  name: string;
  nameKey?: string;
  score: number;
  avatar?: string;
}

interface FriendsScreenProps {
  onBack?: () => void;
}

const { t } = useLanguage();
const { toast } = useToast();
const { profile, points } = useUser();
const [searchQuery, setSearchQuery] = useState('');
const [activeTab, setActiveTab] = useState('friends');

// Bo'sh ro'yxat (Haqiqiy backend ulanmaguncha)
const [friends, setFriends] = useState<Friend[]>([]);
const leaderboard: LeaderboardEntry[] = [
  { rank: 1, nameKey: 'friends.you', name: profile?.name || '', score: points },
];

const handleAddFriend = () => {
  if (!searchQuery.trim()) {
    toast({
      title: t('common.error'),
      description: t('friends.enterUsername'),
      variant: "destructive",
    });
    return;
  }
  toast({
    title: t('friends.requestSent'),
    description: `${searchQuery} ${t('friends.requestSentDesc')}`,
  });
  setSearchQuery('');
};

const handleChallenge = (friendName: string) => {
  toast({
    title: t('friends.challengeSent'),
    description: `${friendName} ${t('friends.challengeSentDesc')}`,
  });
};

const getRankIcon = (rank: number) => {
  switch (rank) {
    case 1: return <Crown className="w-5 h-5 text-yellow-400" />;
    case 2: return <Medal className="w-5 h-5 text-gray-400" />;
    case 3: return <Award className="w-5 h-5 text-amber-600" />;
    default: return <span className="text-muted-foreground font-bold">#{rank}</span>;
  }
};

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

return (
  <div className="min-h-screen bg-background pb-28">
    {/* Header */}
    <div className="px-4 pt-6 pb-4 safe-area-top">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={onBack} className="p-2 rounded-full bg-card">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-foreground">{t('friends.title')}</h1>
          <p className="text-sm text-muted-foreground">{t('friends.subtitle')}</p>
        </div>
      </div>

      {/* Search & Add Friend */}
      <div className="flex gap-2 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder={t('friends.search')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button onClick={handleAddFriend} size="icon">
          <UserPlus className="w-4 h-4" />
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="w-full">
          <TabsTrigger value="friends" className="flex-1">
            <Users className="w-4 h-4 mr-2" />
            {t('friends.friendsTab')}
          </TabsTrigger>
          <TabsTrigger value="leaderboard" className="flex-1">
            <Trophy className="w-4 h-4 mr-2" />
            {t('friends.leaderboard')}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="friends" className="mt-4">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="space-y-3"
          >
            {friends.length === 0 ? (
              <div className="text-center py-20 bg-card/30 rounded-3xl border border-dashed border-border">
                <Users className="w-12 h-12 mx-auto mb-4 opacity-20" />
                <p className="text-muted-foreground px-10">
                  {t('friends.noFriends') || "Hozircha do'stlar yo'q. Do'stingizni @username orqali qidirib toping."}
                </p>
              </div>
            ) : friends.map((friend) => (
              <motion.div
                key={friend.id}
                variants={itemVariants}
                className="p-4 rounded-2xl bg-card border border-border/50"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center text-lg font-bold text-primary">
                        {friend.name[0]}
                      </div>
                      <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-card ${friend.status === 'online' ? 'bg-green-500' : 'bg-gray-400'
                        }`} />
                    </div>
                    <div>
                      <p className="font-semibold text-foreground">{friend.name}</p>
                      <p className="text-sm text-muted-foreground">
                        Level {friend.level} • {friend.xp} XP
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleChallenge(friend.name)}
                    className="gap-1"
                  >
                    <Swords className="w-4 h-4" />
                    {t('friends.challenge')}
                  </Button>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </TabsContent>

        <TabsContent value="leaderboard" className="mt-4">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="space-y-2"
          >
            {leaderboard.map((entry, index) => {
              const displayName = entry.nameKey ? t(entry.nameKey) : entry.name;
              const isYou = entry.nameKey === 'friends.you';
              return (
                <motion.div
                  key={entry.rank}
                  variants={itemVariants}
                  className={`p-4 rounded-2xl border ${entry.rank <= 3
                    ? 'bg-gradient-to-r from-primary/10 to-transparent border-primary/30'
                    : 'bg-card border-border/50'
                    } ${isYou ? 'ring-2 ring-primary' : ''}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-8 flex justify-center">
                        {getRankIcon(entry.rank)}
                      </div>
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center font-bold text-primary">
                        {displayName[0]}
                      </div>
                      <div>
                        <p className={`font-semibold ${isYou ? 'text-primary' : 'text-foreground'}`}>
                          {displayName}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-foreground">{entry.score.toLocaleString()}</p>
                      <p className="text-xs text-muted-foreground">XP</p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        </TabsContent>
      </Tabs>
    </div>
  </div>
);
};
