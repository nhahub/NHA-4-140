import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Gauge, Fuel, Zap, Star, ChevronRight, MessageCircle, Sparkles } from 'lucide-react';
import { cn } from '../hooks/utils';

export const CarCard = ({ car }) => {
  const navigate = useNavigate();
  
  const getFieldValue = (obj, ...keys) => {
    for (const key of keys) {
      if (obj[key] !== undefined && obj[key] !== null) return obj[key];
    }
    return 'N/A';
  };

  return (
    <div className="group relative bg-white dark:bg-slate-900 rounded-[2rem] overflow-hidden border border-gray-100 dark:border-slate-800 hover:border-primary/30 transition-all duration-500 hover:shadow-2xl hover:shadow-gray-200/50 dark:hover:shadow-primary/5 card-shadow hover:-translate-y-2">
      {/* Image Container */}
      <div className="relative h-64 overflow-hidden bg-gray-100 dark:bg-slate-800">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-slate-800 dark:to-slate-900 flex items-center justify-center">
          <Sparkles className="w-12 h-12 text-primary/20 animate-pulse" />
        </div>
        <img 
          src={car.url || car.image || 'https://placehold.co/800x600/png?text=No+Image'} 
          alt={`${getFieldValue(car, 'brand', 'Brand')} ${getFieldValue(car, 'model', 'Model')}`}
          crossOrigin="anonymous"
          className="relative z-10 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
          onError={(e) => {
            e.target.style.display = 'none';
          }}
        />
        <div className="absolute top-4 left-4 z-20">
          <div className="px-4 py-2 rounded-xl glass dark:bg-slate-900/80 backdrop-blur-md border-white/20 text-[10px] font-black uppercase tracking-widest text-gray-900 dark:text-white">
            {getFieldValue(car, 'condition', 'Condition', 'condition')}
          </div>
        </div>
        <button className="absolute top-4 right-4 z-20 p-2.5 rounded-xl glass dark:bg-slate-900/80 backdrop-blur-md border-white/20 text-gray-900 dark:text-white hover:text-red-500 transition-colors">
          <Star className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="p-8">
        <div className="flex justify-between items-start mb-4">
          <div>
            <p className="text-[11px] font-black text-primary uppercase tracking-[0.2em] mb-1">{getFieldValue(car, 'brand', 'Brand')}</p>
            <h3 className="text-2xl font-black text-gray-900 dark:text-white tracking-tight group-hover:text-primary transition-colors">{getFieldValue(car, 'model', 'Model')}</h3>
          </div>
          <div className="text-right">
            <p className="text-2xl font-black text-gray-900 dark:text-white tracking-tighter">{getFieldValue(car, 'price', 'Price')}</p>
            <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest">Market Value</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 py-6 border-y border-gray-50 dark:border-slate-800/50 mb-6">
          <div className="flex flex-col items-center space-y-2">
            <div className="p-2 rounded-xl bg-gray-50 dark:bg-slate-800 text-gray-400 dark:text-slate-500 group-hover:text-primary group-hover:bg-primary/5 transition-all">
              <Fuel className="w-4 h-4" />
            </div>
            <span className="text-[10px] font-black text-gray-500 dark:text-slate-400 uppercase tracking-widest">{getFieldValue(car, 'fuel_type', 'fuelType', 'Fuel_Type')}</span>
          </div>
          <div className="flex flex-col items-center space-y-2">
            <div className="p-2 rounded-xl bg-gray-50 dark:bg-slate-800 text-gray-400 dark:text-slate-500 group-hover:text-primary group-hover:bg-primary/5 transition-all">
              <Zap className="w-4 h-4" />
            </div>
            <span className="text-[10px] font-black text-gray-500 dark:text-slate-400 uppercase tracking-widest">{getFieldValue(car, 'transmission', 'Transmission')}</span>
          </div>
          <div className="flex flex-col items-center space-y-2">
            <div className="p-2 rounded-xl bg-gray-50 dark:bg-slate-800 text-gray-400 dark:text-slate-500 group-hover:text-primary group-hover:bg-primary/5 transition-all">
              <Calendar className="w-4 h-4" />
            </div>
            <span className="text-[10px] font-black text-gray-500 dark:text-slate-400 uppercase tracking-widest">{getFieldValue(car, 'year', 'Year')}</span>
          </div>
        </div>

        {/* AI Insight */}
        {car.description && (
          <div className="mb-8 p-4 rounded-2xl bg-primary/5 border border-primary/10 flex items-start space-x-3 group/insight hover:bg-primary/10 transition-colors">
            <Sparkles className="w-4 h-4 text-primary mt-0.5 shrink-0" />
            <p className="text-xs text-gray-600 dark:text-slate-400 leading-relaxed font-medium">
              <span className="font-black text-primary uppercase tracking-tighter mr-1">AI Insight:</span> {car.description.substring(0, 100)}...
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4">
          <button 
            onClick={() => navigate(`/car/${car.id}`)}
            className="flex-1 py-4 px-6 rounded-2xl bg-gray-50 dark:bg-slate-800 border-2 border-transparent hover:border-gray-200 dark:hover:border-slate-700 text-sm font-black text-gray-900 dark:text-white transition-all flex items-center justify-center space-x-2"
          >
            <span>View Details</span>
          </button>
          <button className="py-4 px-6 rounded-2xl ai-gradient text-white shadow-xl shadow-primary/20 hover:shadow-primary/40 transition-all flex items-center justify-center group/btn">
            <MessageCircle className="w-5 h-5 transition-transform group-hover/btn:scale-110" />
          </button>
        </div>
      </div>
    </div>
  );
};

export const BrandCard = ({ brand, isActive, onClick }) => {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex flex-col items-center justify-center p-8 rounded-[2.5rem] transition-all duration-300 border-2 min-w-[140px] group relative overflow-hidden",
        isActive 
          ? "bg-primary/5 border-primary shadow-xl shadow-primary/10 scale-105" 
          : "bg-white dark:bg-slate-900 border-gray-100 dark:border-slate-800 hover:border-primary/30 hover:shadow-2xl hover:shadow-gray-200/50 dark:hover:shadow-none hover:-translate-y-1"
      )}
    >
      {isActive && (
        <div className="absolute top-3 right-3">
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
        </div>
      )}
      <div className={cn(
        "w-16 h-16 mb-4 flex items-center justify-center transition-all duration-500 group-hover:scale-110",
        !isActive && "grayscale opacity-50 group-hover:grayscale-0 group-hover:opacity-100"
      )}>
        <img src={brand.logo} alt={brand.name} crossOrigin="anonymous" className="w-full h-full object-contain" />
      </div>
      <span className={cn(
        "text-sm font-black tracking-tighter uppercase",
        isActive ? "text-primary" : "text-gray-400 dark:text-slate-500 group-hover:text-gray-900 dark:group-hover:text-white"
      )}>
        {brand.name}
      </span>
    </button>
  );
};
