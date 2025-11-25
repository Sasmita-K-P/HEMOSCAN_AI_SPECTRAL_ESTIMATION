
import React, { useState } from 'react';
import { User } from '../types';
import { LogOut, User as UserIcon, Shield, Database, Calendar, Server } from 'lucide-react';
import { storageService } from '../services/storage';

interface ProfileProps {
  user: User;
  onLogout: () => void;
  onUpdateUser: (user: User) => void;
}

const Profile: React.FC<ProfileProps> = ({ user, onLogout, onUpdateUser }) => {
  const [isUpdating, setIsUpdating] = useState(false);

  const handleLogout = () => {
    storageService.logout();
    onLogout();
  };

  const toggleShareData = async () => {
    setIsUpdating(true);
    try {
        const newValue = !user.shareData;
        const updatedUser = { ...user, shareData: newValue };
        await storageService.updateUser(updatedUser);
        onUpdateUser(updatedUser);
    } catch (e) {
        console.error("Failed to update preference", e);
    } finally {
        setIsUpdating(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">My Profile</h2>
      
      {/* User Info Card */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 flex items-start gap-4">
        <div className="bg-teal-50 p-4 rounded-full">
            <UserIcon className="w-8 h-8 text-teal-600" />
        </div>
        <div className="flex-1">
            <h3 className="font-bold text-slate-800 text-lg">{user.email.split('@')[0]}</h3>
            <p className="text-slate-400 text-sm mb-3">{user.email}</p>
            <div className="flex gap-2">
                <span className="bg-slate-100 text-slate-600 px-3 py-1 rounded-full text-xs font-semibold">
                    {user.age} years
                </span>
                <span className="bg-slate-100 text-slate-600 px-3 py-1 rounded-full text-xs font-semibold">
                    {user.gender}
                </span>
            </div>
        </div>
      </div>

      {/* Settings / Info */}
      <div className="bg-white rounded-xl overflow-hidden border border-slate-100 shadow-sm">
        <div className="p-4 border-b border-slate-100 flex items-center gap-3">
            <Database className="w-5 h-5 text-slate-400" />
            <div>
                <p className="text-sm font-semibold text-slate-700">Database Storage</p>
                <p className="text-xs text-slate-400">Data persists locally (Simulating Cloud DB).</p>
            </div>
        </div>
        
        {/* Data Sharing Toggle */}
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
                <Server className="w-5 h-5 text-slate-400" />
                <div>
                    <p className="text-sm font-semibold text-slate-700">Share Anonymous Data</p>
                    <p className="text-xs text-slate-400">Help improve model accuracy.</p>
                </div>
            </div>
            <button 
                onClick={toggleShareData}
                disabled={isUpdating}
                className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors duration-300 ${user.shareData ? 'bg-teal-600' : 'bg-slate-300'} ${isUpdating ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
                <div className={`bg-white w-4 h-4 rounded-full shadow-md transform duration-300 ${user.shareData ? 'translate-x-5' : 'translate-x-0'}`}></div>
            </button>
        </div>

        <div className="p-4 border-b border-slate-100 flex items-center gap-3">
            <Shield className="w-5 h-5 text-slate-400" />
            <div>
                <p className="text-sm font-semibold text-slate-700">Compliance</p>
                <p className="text-xs text-slate-400">Terms accepted on {new Date(user.createdAt).toLocaleDateString()}</p>
            </div>
        </div>
        <div className="p-4 flex items-center gap-3">
             <Calendar className="w-5 h-5 text-slate-400" />
             <div>
                 <p className="text-sm font-semibold text-slate-700">Member Since</p>
                 <p className="text-xs text-slate-400">{new Date(user.createdAt).toLocaleDateString()}</p>
             </div>
         </div>
      </div>

      <button
        onClick={handleLogout}
        className="w-full bg-red-50 text-red-600 font-bold py-3.5 rounded-xl border border-red-100 flex items-center justify-center gap-2 mt-4 active:scale-95 transition-transform"
      >
        <LogOut className="w-4 h-4" /> Sign Out
      </button>

      <p className="text-center text-xs text-slate-300 mt-6 font-mono">
        UUID: {user.id}
      </p>
    </div>
  );
};

export default Profile;
