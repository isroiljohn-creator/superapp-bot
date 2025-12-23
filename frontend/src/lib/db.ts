// lib/db.ts
import axios from 'axios';

// API base URL - .env dan olinadi yoki default
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Tokenni localStorage dan olish
const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

export const db = {
    /**
     * Ma'lumotlarni olish (Select)
     * profiles -> /user/profile
     */
    async select(table: string, params: any = {}) {
        try {
            if (table === 'profiles') {
                const response = await axios.get(`${API_URL}/user/profile`, {
                    headers: getAuthHeaders(),
                });
                return { data: response.data, error: null };
            }

            // Boshqa jadvallar kiritilishi mumkin
            return { data: null, error: `Table ${table} not implemented in wrapper` };
        } catch (error: any) {
            console.error(`Select error (${table}):`, error);
            return { data: null, error: error.response?.data?.detail || error.message };
        }
    },

    /**
     * Ma'lumot qo'shish yoki yangilash (Insert/Update)
     * profiles -> /user/profile (PUT)
     */
    async insert(table: string, data: any) {
        try {
            if (table === 'profiles') {
                const response = await axios.put(`${API_URL}/user/profile`, data, {
                    headers: getAuthHeaders(),
                });
                return { data: response.data, error: null };
            }

            return { data: null, error: `Table ${table} not implemented in wrapper` };
        } catch (error: any) {
            console.error(`Insert error (${table}):`, error);
            return { data: null, error: error.response?.data?.detail || error.message };
        }
    }
};
