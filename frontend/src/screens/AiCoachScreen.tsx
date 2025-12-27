import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';
import { toast } from 'sonner';
import axios from 'axios';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

const API_URL = import.meta.env.VITE_API_URL || 'https://yasha-bot-production.up.railway.app/api/v1';
const CHAT_URL = `${API_URL}/coach/chat`;

export const AiCoachScreen: React.FC = () => {
  const { profile, todayLog } = useUser();
  const { t } = useLanguage();
  const { vibrate } = useHaptic();

  // Safe initialization with error handling
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      console.log('AiCoachScreen: Initializing messages');
      const greeting = t('aiCoach.greeting') || 'Salom';
      const intro = t('aiCoach.intro') || 'Sizga qanday yordam bera olaman?';
      return [{
        id: '1',
        role: 'assistant',
        content: `${greeting}${profile?.name ? `, ${profile.name}` : ''}! 👋 ${intro}`
      }];
    } catch (error) {
      console.error('AiCoachScreen: Error initializing messages', error);
      return [{
        id: '1',
        role: 'assistant',
        content: 'Salom! 👋 Sizga qanday yordam bera olaman?'
      }];
    }
  });
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const submitQuestion = async (text: string) => {
    if (!text.trim() || isLoading) return;

    vibrate('light');
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(CHAT_URL, {
        messages: messages.filter(m => m.role !== 'assistant' || m.id !== '1').concat(userMessage).map(m => ({
          role: m.role,
          content: m.content
        })),
        userContext: {
          name: profile?.name,
          age: profile?.age,
          goal: profile?.goal,
          todayWater: todayLog?.water_ml,
          todaySteps: todayLog?.steps,
          todaySleep: todayLog?.sleep_hours,
        }
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response && response.data) {
        let replyText = "Tushunarsiz javob.";
        if (response.data.reply && typeof response.data.reply === 'string') {
          replyText = response.data.reply;
        } else if (response.data.reply && typeof response.data.reply === 'object') {
          replyText = JSON.stringify(response.data.reply);
        } else if (typeof response.data === 'string') {
          replyText = response.data;
        }

        const assistantId = (Date.now() + 1).toString();
        setMessages(prev => [...prev, {
          id: assistantId,
          role: 'assistant',
          content: replyText
        }]);
        vibrate('success');
      }

    } catch (error: any) {
      console.error('Chat error:', error);
      toast.error(error.response?.data?.detail || error.message || t('aiCoach.error'));
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = () => submitQuestion(input);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const quickQuestions = [
    t('aiCoach.question1') || 'Bugun nima yeysam bo\'ladi?',
    t('aiCoach.question2') || 'Qanday mashq qilsam yaxshi?',
    t('aiCoach.question3') || 'Kun davomida qancha suv ichishim kerak?'
  ];

  return (
    <div className="h-[var(--tg-viewport-stable-height,100vh)] bg-background flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 safe-area-top border-b border-border/50">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
            <Bot className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">{t('aiCoach.title')}</h1>
            <p className="text-sm text-muted-foreground">{t('aiCoach.subtitle')}</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {(messages.length === 0 && !isLoading) && (
          <div className="text-center py-20 text-muted-foreground">
            <Bot className="w-12 h-12 mx-auto mb-4 opacity-20" />
            <p>{t('aiCoach.noMessages') || 'Xabarlar yo‘q'}</p>
          </div>
        )}

        <AnimatePresence mode="popLayout">
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${message.role === 'user' ? 'bg-primary' : 'bg-primary/20'
                }`}>
                {message.role === 'user' ? (
                  <User className="w-4 h-4 text-primary-foreground" />
                ) : (
                  <Bot className="w-4 h-4 text-primary" />
                )}
              </div>
              <div className={`max-w-[85%] p-3 rounded-2xl ${message.role === 'user'
                ? 'bg-primary text-primary-foreground rounded-br-md shadow-lg shadow-primary/20'
                : 'bg-card border border-border/50 text-foreground rounded-bl-md shadow-sm'
                }`}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3"
          >
            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
              <Loader2 className="w-4 h-4 text-primary animate-spin" />
            </div>
            <div className="bg-card border border-border/50 p-4 rounded-2xl rounded-bl-md">
              <div className="flex gap-1.5">
                <span className="w-1.5 h-1.5 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick questions */}
      {
        messages.length === 1 && (
          <div className="px-4 pb-2">
            <div className="flex gap-2 overflow-x-auto no-scrollbar pb-2">
              {quickQuestions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => {
                    vibrate('light');
                    submitQuestion(q);
                  }}
                  className="px-3 py-2 bg-card border border-border/50 rounded-full text-sm text-foreground whitespace-nowrap hover:bg-muted transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )
      }

      {/* Input */}
      <div className="px-4 pb-4 border-t border-border/50 pt-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={t('aiCoach.placeholder')}
            className="flex-1 h-12 px-4 rounded-full bg-card border border-border/50 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            disabled={isLoading}
          />
          <Button
            size="icon"
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="w-12 h-12 rounded-full"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </Button>
        </div>
      </div>
    </div >
  );
};
