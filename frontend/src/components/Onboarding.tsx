import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, ArrowLeft, Phone, User, Ruler, Target, AlertCircle, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useUser, UserProfile } from '@/contexts/UserContext';
import yashaLogo from '@/assets/yasha-logo.png';

type OnboardingStep = 'welcome' | 'phone' | 'name' | 'body' | 'goal' | 'activity' | 'allergies' | 'complete';

const steps: OnboardingStep[] = ['welcome', 'phone', 'name', 'body', 'goal', 'activity', 'allergies', 'complete'];

const activityLevels = [
  { id: 'sedentary', label: 'Kam harakatli', desc: 'Ofis ishi, kam yurish' },
  { id: 'light', label: 'Engil faol', desc: 'Kunlik 30 daqiqa yurish' },
  { id: 'moderate', label: "O'rtacha faol", desc: 'Haftada 3-4 marta sport' },
  { id: 'active', label: 'Faol', desc: 'Har kuni sport mashqlari' },
  { id: 'very_active', label: 'Juda faol', desc: 'Intensiv mashqlar har kuni' },
];

const goals = [
  { id: 'lose', label: 'Vazn yo\'qotish', icon: '📉', desc: 'Ortiqcha kilolardan xalos bo\'lish' },
  { id: 'gain', label: 'Vazn olish', icon: '📈', desc: 'Mushak massasini oshirish' },
  { id: 'maintain', label: 'Sog\'lom turmush', icon: '⚖️', desc: 'Hozirgi vazningizni saqlash' },
];

const commonAllergies = [
  'Sut mahsulotlari', 'Yong\'oq', 'Tuxum', 'Gluten', 'Dengiz mahsulotlari', 'Soya'
];

export const Onboarding: React.FC = () => {
  const { setProfile, completeOnboarding } = useUser();
  const [currentStep, setCurrentStep] = useState<OnboardingStep>('welcome');
  const [formData, setFormData] = useState({
    phone: '',
    name: '',
    age: '',
    gender: 'male' as 'male' | 'female',
    height: '',
    weight: '',
    goal: '' as 'lose' | 'gain' | 'maintain' | '',
    activityLevel: '' as UserProfile['activityLevel'] | '',
    allergies: [] as string[],
  });

  const currentIndex = steps.indexOf(currentStep);
  const progress = ((currentIndex) / (steps.length - 1)) * 100;

  const goNext = () => {
    const nextIndex = currentIndex + 1;
    if (nextIndex < steps.length) {
      setCurrentStep(steps[nextIndex]);
    }
  };

  const goBack = () => {
    const prevIndex = currentIndex - 1;
    if (prevIndex >= 0) {
      setCurrentStep(steps[prevIndex]);
    }
  };

  const handleComplete = () => {
    const profile: UserProfile = {
      phone: formData.phone,
      name: formData.name,
      age: parseInt(formData.age) || 25,
      gender: formData.gender,
      height: parseInt(formData.height) || 170,
      weight: parseInt(formData.weight) || 70,
      goal: formData.goal as 'lose' | 'gain' | 'maintain',
      activityLevel: formData.activityLevel as UserProfile['activityLevel'],
      allergies: formData.allergies,
    };
    setProfile(profile);
    completeOnboarding();
  };

  const toggleAllergy = (allergy: string) => {
    setFormData(prev => ({
      ...prev,
      allergies: prev.allergies.includes(allergy)
        ? prev.allergies.filter(a => a !== allergy)
        : [...prev.allergies, allergy],
    }));
  };

  const slideVariants = {
    enter: { x: 50, opacity: 0 },
    center: { x: 0, opacity: 1 },
    exit: { x: -50, opacity: 0 },
  };

  return (
    <div className="min-h-screen bg-background flex flex-col safe-area-top safe-area-bottom">
      {/* Progress bar */}
      {currentStep !== 'welcome' && currentStep !== 'complete' && (
        <div className="px-4 pt-4">
          <div className="h-1 bg-muted rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-primary rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>
      )}

      {/* Back button */}
      {currentIndex > 0 && currentStep !== 'complete' && (
        <button
          onClick={goBack}
          className="absolute top-4 left-4 p-2 text-muted-foreground hover:text-foreground z-10"
        >
          <ArrowLeft className="w-6 h-6" />
        </button>
      )}

      {/* Content */}
      <div className="flex-1 flex flex-col px-6 py-8">
        <AnimatePresence mode="wait">
          {/* Welcome */}
          {currentStep === 'welcome' && (
            <motion.div
              key="welcome"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col items-center justify-center text-center"
            >
              <motion.img
                src={yashaLogo}
                alt="YASHA AI"
                className="w-32 h-32 mb-8"
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2 }}
              />
              <h1 className="text-3xl font-display font-bold text-foreground mb-3">
                YASHA AI
              </h1>
              <p className="text-lg text-primary font-medium mb-2">
                Sog'lom Hayot Murabbiyi
              </p>
              <p className="text-muted-foreground max-w-xs mb-8">
                Shaxsiy AI fitnes va dieta murabbiyi. Sog'lom hayot yo'lingizda biz bilan boring!
              </p>
              <Button variant="hero" size="xl" onClick={goNext} className="w-full max-w-xs">
                Boshlash
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Phone */}
          {currentStep === 'phone' && (
            <motion.div
              key="phone"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center mb-6">
                <Phone className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                Telefon raqamingiz
              </h2>
              <p className="text-muted-foreground mb-8">
                Hisobingizni yaratish uchun telefon raqamingizni kiriting
              </p>
              <Input
                type="tel"
                placeholder="+998 90 123 45 67"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="text-lg h-14 mb-4"
              />
              <div className="flex-1" />
              <Button
                variant="hero"
                size="lg"
                onClick={goNext}
                disabled={formData.phone.length < 9}
                className="w-full"
              >
                Davom etish
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Name */}
          {currentStep === 'name' && (
            <motion.div
              key="name"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center mb-6">
                <User className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                Sizni qanday chaqiramiz?
              </h2>
              <p className="text-muted-foreground mb-8">
                Ismingizni kiriting
              </p>
              <Input
                type="text"
                placeholder="Ismingiz"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="text-lg h-14 mb-4"
              />
              <div className="flex-1" />
              <Button
                variant="hero"
                size="lg"
                onClick={goNext}
                disabled={formData.name.length < 2}
                className="w-full"
              >
                Davom etish
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Body metrics */}
          {currentStep === 'body' && (
            <motion.div
              key="body"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center mb-6">
                <Ruler className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                Jismoniy ko'rsatkichlar
              </h2>
              <p className="text-muted-foreground mb-8">
                Sizga mos rejani tuzish uchun kerak
              </p>

              {/* Gender */}
              <div className="flex gap-3 mb-6">
                {[
                  { id: 'male', label: 'Erkak', icon: '👨' },
                  { id: 'female', label: 'Ayol', icon: '👩' },
                ].map((g) => (
                  <button
                    key={g.id}
                    onClick={() => setFormData({ ...formData, gender: g.id as 'male' | 'female' })}
                    className={`flex-1 p-4 rounded-xl border-2 transition-all ${
                      formData.gender === g.id
                        ? 'border-primary bg-primary/10'
                        : 'border-border bg-card'
                    }`}
                  >
                    <span className="text-2xl mb-1 block">{g.icon}</span>
                    <span className="font-medium text-foreground">{g.label}</span>
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-3 gap-3 mb-6">
                <div>
                  <label className="text-sm text-muted-foreground mb-2 block">Yosh</label>
                  <Input
                    type="number"
                    placeholder="25"
                    value={formData.age}
                    onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                    className="h-12 text-center"
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground mb-2 block">Bo'y (sm)</label>
                  <Input
                    type="number"
                    placeholder="170"
                    value={formData.height}
                    onChange={(e) => setFormData({ ...formData, height: e.target.value })}
                    className="h-12 text-center"
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground mb-2 block">Vazn (kg)</label>
                  <Input
                    type="number"
                    placeholder="70"
                    value={formData.weight}
                    onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
                    className="h-12 text-center"
                  />
                </div>
              </div>

              <div className="flex-1" />
              <Button
                variant="hero"
                size="lg"
                onClick={goNext}
                disabled={!formData.age || !formData.height || !formData.weight}
                className="w-full"
              >
                Davom etish
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Goal */}
          {currentStep === 'goal' && (
            <motion.div
              key="goal"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center mb-6">
                <Target className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                Maqsadingiz nima?
              </h2>
              <p className="text-muted-foreground mb-8">
                Asosiy maqsadingizni tanlang
              </p>

              <div className="space-y-3">
                {goals.map((goal) => (
                  <button
                    key={goal.id}
                    onClick={() => setFormData({ ...formData, goal: goal.id as 'lose' | 'gain' | 'maintain' })}
                    className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                      formData.goal === goal.id
                        ? 'border-primary bg-primary/10'
                        : 'border-border bg-card'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{goal.icon}</span>
                      <div>
                        <h3 className="font-semibold text-foreground">{goal.label}</h3>
                        <p className="text-sm text-muted-foreground">{goal.desc}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              <div className="flex-1" />
              <Button
                variant="hero"
                size="lg"
                onClick={goNext}
                disabled={!formData.goal}
                className="w-full"
              >
                Davom etish
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Activity */}
          {currentStep === 'activity' && (
            <motion.div
              key="activity"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col"
            >
              <h2 className="text-2xl font-bold text-foreground mb-2">
                Faollik darajangiz
              </h2>
              <p className="text-muted-foreground mb-6">
                Kundalik faolligingizni tanlang
              </p>

              <div className="space-y-2 flex-1 overflow-auto">
                {activityLevels.map((level) => (
                  <button
                    key={level.id}
                    onClick={() => setFormData({ ...formData, activityLevel: level.id as UserProfile['activityLevel'] })}
                    className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                      formData.activityLevel === level.id
                        ? 'border-primary bg-primary/10'
                        : 'border-border bg-card'
                    }`}
                  >
                    <h3 className="font-semibold text-foreground">{level.label}</h3>
                    <p className="text-sm text-muted-foreground">{level.desc}</p>
                  </button>
                ))}
              </div>

              <Button
                variant="hero"
                size="lg"
                onClick={goNext}
                disabled={!formData.activityLevel}
                className="w-full mt-4"
              >
                Davom etish
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Allergies */}
          {currentStep === 'allergies' && (
            <motion.div
              key="allergies"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center mb-6">
                <AlertCircle className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                Allergiyalaringiz bormi?
              </h2>
              <p className="text-muted-foreground mb-8">
                Tanlang yoki o'tkazib yuboring
              </p>

              <div className="flex flex-wrap gap-2 mb-6">
                {commonAllergies.map((allergy) => (
                  <button
                    key={allergy}
                    onClick={() => toggleAllergy(allergy)}
                    className={`px-4 py-2 rounded-full border-2 transition-all ${
                      formData.allergies.includes(allergy)
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-border bg-card text-foreground'
                    }`}
                  >
                    {allergy}
                  </button>
                ))}
              </div>

              <div className="flex-1" />
              <Button variant="hero" size="lg" onClick={goNext} className="w-full">
                {formData.allergies.length > 0 ? 'Davom etish' : 'O\'tkazib yuborish'}
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Complete */}
          {currentStep === 'complete' && (
            <motion.div
              key="complete"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col items-center justify-center text-center"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
                className="w-24 h-24 rounded-full bg-primary/20 flex items-center justify-center mb-6"
              >
                <Sparkles className="w-12 h-12 text-primary" />
              </motion.div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                Tabriklaymiz, {formData.name}! 🎉
              </h2>
              <p className="text-muted-foreground mb-4 max-w-xs">
                Sizga 7 kunlik bepul Premium sinov berildi!
              </p>
              <div className="bg-primary/10 border border-primary/30 rounded-2xl p-4 mb-8 max-w-xs">
                <p className="text-sm text-foreground">
                  <strong>Premium imkoniyatlar:</strong>
                </p>
                <ul className="text-sm text-muted-foreground mt-2 space-y-1">
                  <li>✓ AI bilan shaxsiy menyu</li>
                  <li>✓ AI mashq dasturi</li>
                  <li>✓ Murabbiy chat</li>
                  <li>✓ Muzlatgich retseptlari</li>
                </ul>
              </div>
              <Button variant="hero" size="xl" onClick={handleComplete} className="w-full max-w-xs">
                Boshlash
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
