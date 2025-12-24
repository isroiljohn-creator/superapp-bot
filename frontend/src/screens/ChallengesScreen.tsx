import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Swords, Plus, ArrowLeft, Footprints, Droplets, Dumbbell, Scale, Users, Clock, Trophy } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useLanguage } from '@/contexts/LanguageContext';
import { useToast } from '@/hooks/use-toast';

interface Challenge {
  id: string;
  title: string;
  type: 'steps' | 'water' | 'workout' | 'weight';
  targetValue: number;
  currentValue: number;
  participants: number;
  daysLeft: number;
  creatorName: string;
  isCreator?: boolean;
}

interface ChallengesScreenProps {
  onBack?: () => void;
}

export const ChallengesScreen: React.FC<ChallengesScreenProps> = ({ onBack }) => {
  const { t } = useLanguage();
  const { toast } = useToast();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newChallenge, setNewChallenge] = useState({
    title: '',
    type: 'steps',
    targetValue: '',
    days: '7',
  });

  // Demo challenge'lar
  const challenges: Challenge[] = [
    { id: '1', title: '10K challenge', type: 'steps', targetValue: 70000, currentValue: 45000, participants: 5, daysLeft: 3, creatorName: 'Aziz' },
    { id: '2', title: t('challenges.water'), type: 'water', targetValue: 17500, currentValue: 12500, participants: 8, daysLeft: 5, creatorName: 'Malika' },
    { id: '3', title: t('challenges.workouts'), type: 'workout', targetValue: 7, currentValue: 4, participants: 3, daysLeft: 2, creatorName: '', isCreator: true },
  ];

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'steps': return <Footprints className="w-5 h-5 text-orange-400" />;
      case 'water': return <Droplets className="w-5 h-5 text-blue-400" />;
      case 'workout': return <Dumbbell className="w-5 h-5 text-purple-400" />;
      case 'weight': return <Scale className="w-5 h-5 text-green-400" />;
      default: return <Swords className="w-5 h-5" />;
    }
  };

  const getTypeUnit = (type: string) => {
    switch (type) {
      case 'steps': return t('challenges.step');
      case 'water': return 'ml';
      case 'workout': return t('challenges.workout');
      case 'weight': return 'kg';
      default: return '';
    }
  };

  const handleCreateChallenge = () => {
    if (!newChallenge.title || !newChallenge.targetValue) {
      toast({
        title: t('common.error'),
        description: t('challenges.fillAll'),
        variant: "destructive",
      });
      return;
    }
    toast({
      title: t('challenges.created'),
      description: `"${newChallenge.title}" ${t('challenges.createdDesc')}`,
    });
    setIsCreateOpen(false);
    setNewChallenge({ title: '', type: 'steps', targetValue: '', days: '7' });
  };

  const handleJoinChallenge = (challengeTitle: string) => {
    toast({
      title: t('challenges.joined'),
      description: `"${challengeTitle}" ${t('challenges.joinedDesc')}`,
    });
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
    <div className="min-h-screen bg-background pb-24">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <button onClick={onBack} className="p-2 rounded-full bg-card">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl font-bold text-foreground">{t('challenges.title')}</h1>
              <p className="text-sm text-muted-foreground">{t('challenges.subtitle')}</p>
            </div>
          </div>
          
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button size="icon">
                <Plus className="w-5 h-5" />
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('challenges.new')}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <Input
                  placeholder={t('challenges.name')}
                  value={newChallenge.title}
                  onChange={(e) => setNewChallenge({ ...newChallenge, title: e.target.value })}
                />
                <Select
                  value={newChallenge.type}
                  onValueChange={(value) => setNewChallenge({ ...newChallenge, type: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={t('challenges.type')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="steps">{t('challenges.steps')}</SelectItem>
                    <SelectItem value="water">{t('challenges.water')}</SelectItem>
                    <SelectItem value="workout">{t('challenges.workouts')}</SelectItem>
                    <SelectItem value="weight">{t('challenges.weight')}</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  type="number"
                  placeholder={t('challenges.targetValue')}
                  value={newChallenge.targetValue}
                  onChange={(e) => setNewChallenge({ ...newChallenge, targetValue: e.target.value })}
                />
                <Select
                  value={newChallenge.days}
                  onValueChange={(value) => setNewChallenge({ ...newChallenge, days: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={t('challenges.duration')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="3">{t('challenges.3days')}</SelectItem>
                    <SelectItem value="7">{t('challenges.7days')}</SelectItem>
                    <SelectItem value="14">{t('challenges.14days')}</SelectItem>
                    <SelectItem value="30">{t('challenges.30days')}</SelectItem>
                  </SelectContent>
                </Select>
                <Button className="w-full" onClick={handleCreateChallenge}>
                  <Swords className="w-4 h-4 mr-2" />
                  {t('challenges.create')}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Active Challenges */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="space-y-4"
        >
          <h2 className="text-lg font-bold text-foreground">{t('challenges.active')}</h2>
          
          {challenges.map((challenge) => {
            const progress = (challenge.currentValue / challenge.targetValue) * 100;
            
            return (
              <motion.div
                key={challenge.id}
                variants={itemVariants}
                className="p-4 rounded-2xl bg-card border border-border/50"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-primary/10">
                      {getTypeIcon(challenge.type)}
                    </div>
                    <div>
                      <p className="font-semibold text-foreground">{challenge.title}</p>
                      <p className="text-sm text-muted-foreground">
                        @{challenge.isCreator ? t('friends.you') : challenge.creatorName}
                      </p>
                    </div>
                  </div>
                  {!challenge.isCreator && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleJoinChallenge(challenge.title)}
                    >
                      {t('challenges.join')}
                    </Button>
                  )}
                </div>

                {/* Progress */}
                <div className="mb-3">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">{t('challenges.progress')}</span>
                    <span className="font-medium text-foreground">
                      {challenge.currentValue.toLocaleString()} / {challenge.targetValue.toLocaleString()} {getTypeUnit(challenge.type)}
                    </span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-primary to-primary/70 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(progress, 100)}%` }}
                      transition={{ duration: 1, ease: "easeOut" }}
                    />
                  </div>
                </div>

                {/* Stats */}
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    <span>{challenge.participants} {t('challenges.participants')}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>{challenge.daysLeft} {t('challenges.daysLeft')}</span>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </div>
  );
};
