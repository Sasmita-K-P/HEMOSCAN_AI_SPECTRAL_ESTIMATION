import React, { useState } from 'react';
import { Activity, Mail, Lock, User as UserIcon, Calendar, ArrowRight, Loader2, CheckSquare, Eye, EyeOff } from 'lucide-react';
import { storageService } from '../services/storage';
import { User } from '../types';

interface AuthProps {
  onLogin: (user: User) => void;
}

const Auth: React.FC<AuthProps> = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Form State
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState<'Male' | 'Female' | 'Other'>('Male');
  const [termsAccepted, setTermsAccepted] = useState(false);

  const validateEmail = (email: string) => {
    // Robust email regex: checks for alphanumeric characters, proper domain part, and TLD of at least 2 chars
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    // 1. Strict Email Validation
    if (!validateEmail(email)) {
      setError("Please enter a valid email address.");
      return;
    }

    // 2. Password Length Check (Basic Security)
    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    if (!isLogin && !termsAccepted) {
      setError("You must agree to the Terms & Privacy Policy to continue.");
      return;
    }

    setIsLoading(true);

    try {
      let user: User;
      if (isLogin) {
        user = await storageService.login(email, password);
      } else {
        if (!age || parseInt(age) < 0 || parseInt(age) > 120) {
            throw new Error("Please enter a valid age.");
        }
        user = await storageService.register(email, password, parseInt(age), gender, termsAccepted);
      }
      onLogin(user);
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-600 via-teal-500 to-emerald-500 flex flex-col items-center justify-center p-6 relative overflow-hidden">
      
      {/* Background Decor */}
      <div className="absolute top-[-10%] left-[-10%] w-64 h-64 bg-white/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-80 h-80 bg-teal-900/20 rounded-full blur-3xl"></div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo Area */}
        <div className="flex flex-col items-center mb-8 animate-fade-in-down">
          <div className="bg-white/20 backdrop-blur-md p-4 rounded-2xl shadow-xl border border-white/20 mb-4 ring-4 ring-white/10">
            <Activity className="text-white w-12 h-12" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight drop-shadow-sm">HemoScan AI</h1>
          <p className="text-teal-50 text-sm mt-1 font-medium">Clinical-grade anemia screening</p>
        </div>

        {/* Auth Card */}
        <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl shadow-teal-900/20 p-8 transition-all duration-300">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-slate-800">
              {isLogin ? 'Welcome Back' : 'Create Account'}
            </h2>
            <div className="h-1.5 w-12 bg-gradient-to-r from-teal-500 to-emerald-400 rounded-full"></div>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-600 text-sm rounded-r-lg flex items-start gap-3 shadow-sm animate-shake">
              <span className="font-bold text-lg leading-none">•</span>
              <span className="font-medium">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Email Address</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="w-5 h-5 text-slate-400 group-focus-within:text-teal-500 transition-colors" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-xl focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 outline-none transition-all text-sm font-medium text-slate-800 placeholder-slate-400"
                  placeholder="name@example.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Password</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="w-5 h-5 text-slate-400 group-focus-within:text-teal-500 transition-colors" />
                </div>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-12 py-3.5 bg-slate-50 border border-slate-200 rounded-xl focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 outline-none transition-all text-sm font-medium text-slate-800 placeholder-slate-400"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {!isLogin && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Age</label>
                    <div className="relative group">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Calendar className="w-5 h-5 text-slate-400 group-focus-within:text-teal-500 transition-colors" />
                      </div>
                      <input
                        type="number"
                        required
                        value={age}
                        onChange={(e) => setAge(e.target.value)}
                        className="w-full pl-10 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-xl focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 outline-none transition-all text-sm font-medium"
                        placeholder="Age"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Gender</label>
                    <div className="relative group">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <UserIcon className="w-5 h-5 text-slate-400 group-focus-within:text-teal-500 transition-colors" />
                      </div>
                      <select
                        value={gender}
                        onChange={(e) => setGender(e.target.value as any)}
                        className="w-full pl-10 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-xl focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 outline-none transition-all text-sm font-medium text-slate-800 appearance-none"
                      >
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                      </select>
                      <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                        <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl border border-slate-100 hover:border-slate-200 transition-colors cursor-pointer" onClick={() => setTermsAccepted(!termsAccepted)}>
                  <div className={`mt-0.5 w-5 h-5 rounded border flex items-center justify-center transition-all ${termsAccepted ? 'bg-teal-600 border-teal-600' : 'bg-white border-slate-300'}`}>
                    {termsAccepted && <CheckSquare className="w-3.5 h-3.5 text-white" />}
                  </div>
                  <label className="text-xs text-slate-600 leading-relaxed cursor-pointer select-none">
                    I consent to the collection of my nail data for analysis and agree to the <span className="text-teal-600 font-bold hover:underline">Terms & Privacy Policy</span>.
                  </label>
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-teal-600/30 active:scale-[0.98] transition-all flex items-center justify-center gap-2 mt-4 group"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  {isLogin ? 'Sign In' : 'Create Account'} 
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Toggle Mode */}
        <div className="text-center mt-8">
          <p className="text-teal-100/80 text-sm font-medium">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
          </p>
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="mt-2 px-6 py-2 bg-white/10 hover:bg-white/20 text-white rounded-full text-sm font-bold backdrop-blur-sm transition-all border border-white/10"
          >
            {isLogin ? 'Register New Account' : 'Log In to Existing'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Auth;