import { useState } from 'react'
import { useUserStore } from '../store/userStore'
import api from '../api/client'
import { Check, Loader2, Shield } from 'lucide-react'

export default function Premium() {
    const { user, setUser } = useUserStore()
    const [loading, setLoading] = useState(false)

    const handlePurchase = async (packageId: string) => {
        setLoading(true)
        try {
            await api.post('/pay/mock', { package: packageId })

            // Refresh user profile
            const res = await api.get('/user/profile')
            setUser(res.data)

            alert('Premium muvaffaqiyatli faollashtirildi! 🎉')
        } catch (error) {
            console.error(error)
            alert('Xatolik yuz berdi.')
        } finally {
            setLoading(false)
        }
    }

    if (user?.is_premium) {
        return (
            <div className="min-h-screen bg-black text-white p-6 flex flex-col items-center justify-center text-center">
                <div className="w-24 h-24 bg-[#C8FF00]/20 rounded-full flex items-center justify-center mb-6">
                    <Shield className="text-[#C8FF00] w-12 h-12" />
                </div>
                <h1 className="text-3xl font-bold mb-2">Premium Aktiv!</h1>
                <p className="text-gray-400 mb-8">
                    Sizning obunangiz {new Date(user.premium_until || '').toLocaleDateString()} gacha amal qiladi.
                </p>
                <button
                    onClick={() => window.history.back()}
                    className="w-full py-4 bg-[#1A1A1A] text-white rounded-xl font-bold"
                >
                    Orqaga
                </button>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-3xl font-bold mb-2">Premium Olish</h1>
            <p className="text-gray-400 mb-8">Barcha imkoniyatlardan cheklovsiz foydalaning.</p>

            <div className="space-y-4">
                {/* 1 Month Plan */}
                <div className="bg-[#1A1A1A] rounded-2xl p-6 border border-gray-800 relative overflow-hidden">
                    <div className="relative z-10">
                        <h3 className="text-xl font-bold mb-1">1 Oy</h3>
                        <p className="text-2xl font-bold text-[#C8FF00] mb-4">49 000 so'm</p>
                        <ul className="space-y-2 mb-6 text-sm text-gray-300">
                            <li className="flex gap-2"><Check size={16} className="text-[#C8FF00]" /> Cheksiz AI Rejalar</li>
                            <li className="flex gap-2"><Check size={16} className="text-[#C8FF00]" /> Kengaytirilgan Statistika</li>
                            <li className="flex gap-2"><Check size={16} className="text-[#C8FF00]" /> Reklamasiz</li>
                        </ul>
                        <button
                            onClick={() => handlePurchase('premium_30')}
                            disabled={loading}
                            className="w-full py-3 bg-white text-black rounded-xl font-bold hover:bg-gray-200 transition-colors"
                        >
                            {loading ? <Loader2 className="animate-spin mx-auto" /> : 'Sotib Olish'}
                        </button>
                    </div>
                </div>

                {/* 3 Month Plan */}
                <div className="bg-gradient-to-br from-[#C8FF00]/20 to-[#1A1A1A] rounded-2xl p-6 border border-[#C8FF00]/50 relative overflow-hidden">
                    <div className="absolute top-0 right-0 bg-[#C8FF00] text-black text-xs font-bold px-3 py-1 rounded-bl-xl">
                        ENG FOYDALI
                    </div>
                    <div className="relative z-10">
                        <h3 className="text-xl font-bold mb-1">3 Oy</h3>
                        <p className="text-2xl font-bold text-[#C8FF00] mb-4">119 000 so'm</p>
                        <ul className="space-y-2 mb-6 text-sm text-gray-300">
                            <li className="flex gap-2"><Check size={16} className="text-[#C8FF00]" /> Barcha 1 oylik imkoniyatlar</li>
                            <li className="flex gap-2"><Check size={16} className="text-[#C8FF00]" /> 20% Chegirma</li>
                            <li className="flex gap-2"><Check size={16} className="text-[#C8FF00]" /> Ustuvor qo'llab-quvvatlash</li>
                        </ul>
                        <button
                            onClick={() => handlePurchase('premium_90')}
                            disabled={loading}
                            className="w-full py-3 bg-[#C8FF00] text-black rounded-xl font-bold hover:bg-[#b3e600] transition-colors"
                        >
                            {loading ? <Loader2 className="animate-spin mx-auto" /> : 'Sotib Olish'}
                        </button>
                    </div>
                </div>
            </div>

            <p className="text-center text-xs text-gray-500 mt-8">
                To'lov xavfsiz amalga oshiriladi (Test rejimi).
            </p>
        </div>
    )
}
