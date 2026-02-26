import { useEffect, useState } from 'react'
import { getProfile, type UserProfile } from '../api/client'

export default function Dashboard() {
    const [profile, setProfile] = useState<UserProfile | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        getProfile()
            .then(setProfile)
            .catch(() => { })
            .finally(() => setLoading(false))
    }, [])

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner" />
            </div>
        )
    }

    if (!profile) {
        return (
            <div className="page">
                <p style={{ textAlign: 'center', color: 'var(--tg-hint)' }}>
                    Ma'lumotlar yuklanmadi
                </p>
            </div>
        )
    }

    const goalLabels: Record<string, string> = {
        make_money: '💰 Pul topish',
        get_clients: '👥 Mijoz olish',
        automate_business: '⚙️ Avtomatlashtirish',
    }

    const levelLabels: Record<string, string> = {
        beginner: '🌱 Boshlang\'ich',
        freelancer: '💼 Frilanser',
        business: '🏢 Biznes',
    }

    return (
        <div className="page">
            <h1 className="page-title">
                👋 Salom, {profile.name || 'Foydalanuvchi'}!
            </h1>

            {/* Subscription Status */}
            <div className="card">
                <div className="card-header">
                    <span className="card-icon">
                        {profile.subscription_status === 'active' ? '💎' : '🔒'}
                    </span>
                    <span className="card-title">Obuna holati</span>
                </div>
                <div style={{
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-sm)',
                    background: profile.subscription_status === 'active'
                        ? 'rgba(16, 185, 129, 0.15)'
                        : 'rgba(239, 68, 68, 0.15)',
                    textAlign: 'center',
                    fontWeight: 700,
                    color: profile.subscription_status === 'active' ? '#34d399' : '#f87171',
                }}>
                    {profile.subscription_status === 'active' ? '✅ Faol' : '❌ Faol emas'}
                </div>
            </div>

            {/* Stats */}
            <div className="card">
                <div className="card-header">
                    <span className="card-icon">📊</span>
                    <span className="card-title">Statistika</span>
                </div>
                <div className="stats-grid">
                    <div className="stat-item">
                        <div className="stat-value">{profile.lead_score}</div>
                        <div className="stat-label">Ball</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">
                            {profile.lead_segment === 'hot' ? '🔥' : profile.lead_segment === 'nurture' ? '📈' : '📋'}
                        </div>
                        <div className="stat-label">{
                            profile.lead_segment === 'hot' ? 'Issiq lead' :
                                profile.lead_segment === 'nurture' ? 'Rivojlantirish' : 'Kontent'
                        }</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{goalLabels[profile.goal_tag || ''] || '—'}</div>
                        <div className="stat-label">Maqsad</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{levelLabels[profile.level_tag || ''] || '—'}</div>
                        <div className="stat-label">Daraja</div>
                    </div>
                </div>
            </div>

            {/* Next Action */}
            <div className="card">
                <div className="card-header">
                    <span className="card-icon">🎯</span>
                    <span className="card-title">Keyingi qadam</span>
                </div>
                <p style={{ color: 'var(--tg-hint)', fontSize: 14, lineHeight: 1.6 }}>
                    {profile.subscription_status === 'active'
                        ? 'Klub darslarini davom ettiring va do\'stlaringizni taklif qiling!'
                        : 'Bepul kursni ko\'ring va klubga qo\'shiling!'}
                </p>
            </div>
        </div>
    )
}
