import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Users, Copy, Check } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

export default function ReferralTab() {
    const { user } = useAuth();
    const [copied, setCopied] = React.useState(false);

    const telegramId = user?.id;
    const botUsername = "YashaFitnessBot"; // Hardcoded or from ENV
    const referralLink = `https://t.me/${botUsername}?start=${telegramId || ''}`;

    const handleCopy = () => {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(referralLink);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <div className="space-y-4 p-4 pb-20">
            <Card className="bg-gradient-to-br from-indigo-900 to-purple-900 border-none text-white">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Users className="w-6 h-6" />
                        Do'stlarni Taklif Qilish
                    </CardTitle>
                    <CardDescription className="text-gray-200">
                        Do'stlaringizni taklif qiling va bepul Premium kunlarga ega bo'ling!
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="bg-black/20 p-4 rounded-lg mb-4">
                        <p className="text-sm text-gray-300 mb-1">Sizning havolangiz:</p>
                        <code className="block w-full bg-black/40 p-2 rounded text-xs break-all font-mono text-blue-300">
                            {referralLink}
                        </code>
                    </div>

                    <Button
                        onClick={handleCopy}
                        className="w-full bg-white text-purple-900 hover:bg-gray-100 font-bold"
                    >
                        {copied ? (
                            <>
                                <Check className="w-4 h-4 mr-2" /> Nusxalandi
                            </>
                        ) : (
                            <>
                                <Copy className="w-4 h-4 mr-2" /> Havoladan nusxa olish
                            </>
                        )}
                    </Button>

                    <div className="mt-6 space-y-2 text-sm text-gray-300">
                        <p>🎁 <b>Bonuslar:</b></p>
                        <ul className="list-disc pl-5 space-y-1">
                            <li>Har bir do'stingiz uchun +5 kun Premium</li>
                            <li>Do'stingiz uchun 7 kunlik bepul sinov davri</li>
                            <li>Eng faol taklif qiluvchilar uchun maxsus sovrinlar</li>
                        </ul>
                    </div>
                </CardContent>
            </Card>

            {/* Instructions or Leaderboard teaser could go here */}
        </div>
    );
}
