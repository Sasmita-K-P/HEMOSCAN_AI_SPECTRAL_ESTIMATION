
import { User, AnalysisResult } from "../types";
import { generateUUID } from "../utils/uuid";

// Keys for LocalStorage - Simulating Database Tables
const USERS_TABLE = 'hemoscan_users_table';
const CURRENT_SESSION_KEY = 'hemoscan_current_session';
const HISTORY_TABLE_PREFIX = 'hemoscan_history_';

/**
 * DATABASE ADAPTER
 * 
 * In a production environment (Python + NeonDB/Supabase), 
 * replace the localStorage calls below with actual API/SQL calls.
 * 
 * Example:
 * localStorage.setItem(...) -> await supabase.from('users').insert(...)
 */
export const storageService = {
  // --- Auth / User Management ---

  register: async (email: string, password: string, age: number, gender: 'Male' | 'Female' | 'Other', termsAccepted: boolean): Promise<User> => {
    // Simulate network latency (Realism)
    await new Promise(resolve => setTimeout(resolve, 800));

    const usersStr = localStorage.getItem(USERS_TABLE);
    const users: User[] = usersStr ? JSON.parse(usersStr) : [];

    // DB Constraint Check: Unique Email
    if (users.find(u => u.email === email)) {
      throw new Error("User already exists with this email.");
    }

    const newUser: User = {
      id: generateUUID(),
      email,
      password, // Security Note: In real backend, hash with bcrypt/argon2
      age,
      gender,
      termsAccepted,
      createdAt: Date.now(),
      shareData: false // Default to false (Opt-in)
    };

    // Insert into "Users Table"
    users.push(newUser);
    localStorage.setItem(USERS_TABLE, JSON.stringify(users));
    
    // Create Session
    localStorage.setItem(CURRENT_SESSION_KEY, JSON.stringify(newUser));
    return newUser;
  },

  login: async (email: string, password: string): Promise<User> => {
    await new Promise(resolve => setTimeout(resolve, 800));

    const usersStr = localStorage.getItem(USERS_TABLE);
    const users: User[] = usersStr ? JSON.parse(usersStr) : [];

    // Query User
    const user = users.find(u => u.email === email && u.password === password);
    
    if (!user) {
      throw new Error("Invalid email or password.");
    }

    // Create Session
    localStorage.setItem(CURRENT_SESSION_KEY, JSON.stringify(user));
    return user;
  },

  logout: () => {
    localStorage.removeItem(CURRENT_SESSION_KEY);
  },

  getCurrentUser: (): User | null => {
    const userStr = localStorage.getItem(CURRENT_SESSION_KEY);
    return userStr ? JSON.parse(userStr) : null;
  },

  updateUser: async (updatedUser: User): Promise<void> => {
    // Simulate network latency
    await new Promise(resolve => setTimeout(resolve, 300));

    // Update in Session
    localStorage.setItem(CURRENT_SESSION_KEY, JSON.stringify(updatedUser));

    // Update in Users Table
    const usersStr = localStorage.getItem(USERS_TABLE);
    if (usersStr) {
      let users: User[] = JSON.parse(usersStr);
      users = users.map(u => u.id === updatedUser.id ? updatedUser : u);
      localStorage.setItem(USERS_TABLE, JSON.stringify(users));
    }
  },

  // --- Data / History Management ---

  saveScan: (userId: string, result: AnalysisResult) => {
    const key = HISTORY_TABLE_PREFIX + userId;
    const historyStr = localStorage.getItem(key);
    const history: AnalysisResult[] = historyStr ? JSON.parse(historyStr) : [];
    
    history.push(result);
    localStorage.setItem(key, JSON.stringify(history));
  },

  getUserHistory: (userId: string): AnalysisResult[] => {
    const key = HISTORY_TABLE_PREFIX + userId;
    const historyStr = localStorage.getItem(key);
    return historyStr ? JSON.parse(historyStr) : [];
  }
};
