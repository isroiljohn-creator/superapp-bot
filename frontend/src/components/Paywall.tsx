import React from 'react';
import { motion } from 'framer-motion';
import { Crown, Sparkles, Check, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface PaywallProps {
  isOpen: boolean;
  onClose: () => void;
  feature?: string;
}

const plans = [
  {
    id: 'premium',
    name: 'Premium',
    price: "99,000",
    period: 'oyiga',
    features: [
      '7 kunlik AI menyu',
      '7 kunlik mashq dasturi',
      'AI murabbiy chat',
      'Muzlatgich retseptlari',
      'Savdo ro\'yxati',
    ],
    popular: true,
  },
  {
    id: 'vip',
    name: 'VIP',
    price: "199,000",
    period: 'oyiga',
    features: [
      'Premium barcha imkoniyatlari',
      'Oyiga 4 marta menyu yangilash',
      'Taom almashtirish',
      'Prioritet yordam',
      'Maxsus retseptlar',
    ],
    popular: false,
  },
];

export const Paywall: React.FC<PaywallProps> = ({
  isOpen,
  onClose,
  feature,
}) => {
  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm flex flex-col"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 safe-area-top">
        <button
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground"
        >
          Yopish
        </button>
        <div className="w-16" />
      </div>

      <div className="flex-1 overflow-auto px-4 pb-8">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-primary/20 flex items-center justify-center">
            <Crown className="w-10 h-10 text-primary" />
          </div>
          <h1 className="text-2xl font-display font-bold text-foreground mb-2">
            Premium rejaga o'ting
          </h1>
          {feature && (
            <p className="text-muted-foreground">
              <Lock className="w-4 h-4 inline mr-1" />
              "{feature}" faqat premium uchun
            </p>
          )}
        </motion.div>

        {/* Plans */}
        <div className="space-y-4">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={cn(
                "relative p-5 rounded-2xl border-2 transition-all",
                plan.popular
                  ? "border-primary bg-primary/5"
                  : "border-border bg-card"
              )}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-4 px-3 py-1 bg-primary text-primary-foreground text-xs font-bold rounded-full flex items-center gap-1">
                  <Sparkles className="w-3 h-3" />
                  MASHHUR
                </div>
              )}

              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-bold text-foreground">{plan.name}</h3>
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-bold text-foreground">
                      {plan.price}
                    </span>
                    <span className="text-sm text-muted-foreground">so'm/{plan.period}</span>
                  </div>
                </div>
              </div>

              <ul className="space-y-2 mb-4">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm">
                    <Check className="w-4 h-4 text-primary flex-shrink-0" />
                    <span className="text-foreground">{feature}</span>
                  </li>
                ))}
              </ul>

              <Button
                variant={plan.popular ? "hero" : "outline"}
                className="w-full"
              >
                Tanlash
              </Button>
            </motion.div>
          ))}
        </div>

        {/* Trial notice */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-center text-sm text-muted-foreground mt-6"
        >
          7 kunlik bepul sinov • Istalgan vaqtda bekor qilish mumkin
        </motion.p>
      </div>
    </motion.div>
  );
};
