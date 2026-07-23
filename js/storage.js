/* storage.js — persist an in-progress exam to localStorage */

const Storage = {
    save(state) {
        try {
            localStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(state));
        } catch (_) {
            /* storage full or unavailable — ignore, exam still works in-memory */
        }
    },

    load() {
        try {
            const raw = localStorage.getItem(CONFIG.STORAGE_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (_) {
            return null;
        }
    },

    clear() {
        try {
            localStorage.removeItem(CONFIG.STORAGE_KEY);
        } catch (_) {
            /* ignore */
        }
    },

    has() {
        return this.load() !== null;
    }
};
