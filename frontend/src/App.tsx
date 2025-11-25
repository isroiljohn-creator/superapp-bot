import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom'
import { Home as HomeIcon, Dumbbell, User } from 'lucide-react'
import { useUserStore } from './store/userStore'
import { authAPI } from './api/client'

import Home from './pages/Home'
import Plan from './pages/Plan'
import Profile from './pages/Profile'

function App() {
    const { token, setToken, setUser } = useUserStore()
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.ready()
            window.Telegram.WebApp.expand()

            // Auth flow
            const initData = window.Telegram.WebApp.initData
            if (initData && !token) {
                authAPI.telegramAuth(initData)
                    .then((res) => {
                        setToken(res.data.token)
                        setUser(res.data.user)
                        setLoading(false)
                    })
                    .catch((err) => {
                        console.error('Auth failed', err)
                        setLoading(false)
                    })
            } else {
                setLoading(false)
            }
        } else {
            setLoading(false)
        }
    }, [])

    if (loading) {
        return <div className="flex items-center justify-center h-screen bg-black text-white">Yuklanmoqda...</div>
    }

    if (!token) {
        return <div className="flex items-center justify-center h-screen bg-black text-white">Autentifikatsiya xatosi</div>
    }

    return (
        <BrowserRouter>
            <div className="pb-20 bg-black min-h-screen">
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/plan" element={<Plan />} />
                    <Route path="/profile" element={<Profile />} />
                    <Route path="*" element={<Navigate to="/" />} />
                </Routes>

                {/* Bottom Nav */}
                <div className="fixed bottom-0 left-0 right-0 bg-[#1A1A1A] border-t border-gray-800 flex justify-around p-3 safe-area-inset-bottom">
                    <Link to="/" className="flex flex-col items-center text-xs text-gray-400 hover:text-[#C8FF00] transition-colors">
                        <HomeIcon size={24} />
                        <span className="mt-1">Bosh</span>
                    </Link>
                    <Link to="/plan" className="flex flex-col items-center text-xs text-gray-400 hover:text-[#C8FF00] transition-colors">
                        <Dumbbell size={24} />
                        <span className="mt-1">Reja</span>
                    </Link>
                    <Link to="/profile" className="flex flex-col items-center text-xs text-gray-400 hover:text-[#C8FF00] transition-colors">
                        <User size={24} />
                        <span className="mt-1">Profil</span>
                    </Link>
                </div>
            </div>
        </BrowserRouter>
    )
}

export default App
