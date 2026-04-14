import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, MapPin, Calendar, Gauge, Fuel, Zap, ShieldCheck, 
  MessageCircle, Star, Share2, Loader2, ChevronRight 
} from 'lucide-react';
import { fetchCar } from '../api/carApi';
import { cn } from '../hooks/utils';

const CarDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [car, setCar] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCar();
  }, [id]);

  const loadCar = async () => {
    try {
      setLoading(true);
      const data = await fetchCar(id);
      setCar(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getFieldValue = (obj, ...keys) => {
    for (const key of keys) {
      if (obj[key] !== undefined && obj[key] !== null) return obj[key];
    }
    return 'N/A';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] dark:bg-slate-950 flex items-center justify-center">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] dark:bg-slate-950 flex flex-col items-center justify-center">
        <p className="text-red-500 mb-4">Error: {error}</p>
        <button 
          onClick={() => navigate('/')}
          className="px-6 py-3 rounded-2xl ai-gradient text-white font-black"
        >
          Back to Marketplace
        </button>
      </div>
    );
  }

  if (!car) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] dark:bg-slate-950 flex flex-col items-center justify-center">
        <p className="text-gray-500 mb-4">Car not found</p>
        <button 
          onClick={() => navigate('/')}
          className="px-6 py-3 rounded-2xl ai-gradient text-white font-black"
        >
          Back to Marketplace
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] dark:bg-slate-950 transition-colors duration-300">
      {/* Hero Image Section */}
      <div className="relative h-[50vh] min-h-[400px] bg-gray-900 overflow-hidden">
        <img 
          src={car.url || 'https://placehold.co/1200x600/png?text=No+Image'}
          alt={`${getFieldValue(car, 'brand', 'Brand')} ${getFieldValue(car, 'model', 'Model')}`}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.target.src = 'https://placehold.co/1200x600/png?text=No+Image';
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/40 to-transparent" />
        
        {/* Back Button */}
        <button 
          onClick={() => navigate(-1)}
          className="absolute top-6 left-6 flex items-center space-x-2 px-4 py-2 rounded-full glass dark:bg-slate-900/80 backdrop-blur-md text-white font-black text-sm hover:scale-105 transition-transform"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>

        {/* Action Buttons */}
        <div className="absolute top-6 right-6 flex space-x-3">
          <button className="p-3 rounded-full glass dark:bg-slate-900/80 backdrop-blur-md text-white hover:text-primary transition-colors">
            <Share2 className="w-5 h-5" />
          </button>
          <button className="p-3 rounded-full glass dark:bg-slate-900/80 backdrop-blur-md text-white hover:text-red-500 transition-colors">
            <Star className="w-5 h-5" />
          </button>
        </div>

        {/* Title Overlay */}
        <div className="absolute bottom-0 left-0 w-full p-8">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center space-x-2 text-primary/80 font-black text-xs uppercase tracking-widest mb-3">
              <span>{getFieldValue(car, 'brand', 'Brand')}</span>
              <ChevronRight className="w-4 h-4" />
              <span>{getFieldValue(car, 'condition', 'Condition', 'condition')}</span>
            </div>
            <h1 className="text-4xl md:text-6xl font-black text-white tracking-tight">
              {getFieldValue(car, 'model', 'Model')}
            </h1>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Price & Key Info */}
            <div className="bg-white dark:bg-slate-900 rounded-[2rem] p-8 border border-gray-100 dark:border-slate-800">
              <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                <div>
                  <p className="text-4xl md:text-5xl font-black text-gray-900 dark:text-white tracking-tighter">
                    {getFieldValue(car, 'price', 'Price')}
                  </p>
                  <p className="text-sm font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mt-1">
                    Listed Price
                  </p>
                </div>
                <div className="px-4 py-2 rounded-xl bg-primary/10 text-primary text-sm font-black uppercase tracking-widest">
                  {getFieldValue(car, 'condition', 'Condition', 'condition')}
                </div>
              </div>

              {/* Specs Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-slate-800/50 text-center">
                  <Calendar className="w-6 h-6 text-primary mx-auto mb-2" />
                  <p className="text-lg font-black text-gray-900 dark:text-white">{getFieldValue(car, 'year', 'Year')}</p>
                  <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest">Year</p>
                </div>
                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-slate-800/50 text-center">
                  <Gauge className="w-6 h-6 text-primary mx-auto mb-2" />
                  <p className="text-lg font-black text-gray-900 dark:text-white">{getFieldValue(car, 'km', 'km', 'KM')}</p>
                  <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest">Mileage</p>
                </div>
                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-slate-800/50 text-center">
                  <Fuel className="w-6 h-6 text-primary mx-auto mb-2" />
                  <p className="text-lg font-black text-gray-900 dark:text-white">{getFieldValue(car, 'fuel_type', 'fuelType', 'Fuel_Type')}</p>
                  <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest">Fuel</p>
                </div>
                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-slate-800/50 text-center">
                  <Zap className="w-6 h-6 text-primary mx-auto mb-2" />
                  <p className="text-lg font-black text-gray-900 dark:text-white">{getFieldValue(car, 'transmission', 'Transmission')}</p>
                  <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest">Transmission</p>
                </div>
              </div>
            </div>

            {/* Additional Details */}
            <div className="bg-white dark:bg-slate-900 rounded-[2rem] p-8 border border-gray-100 dark:border-slate-800">
              <h2 className="text-2xl font-black text-gray-900 dark:text-white tracking-tight mb-6">Vehicle Details</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-slate-800/50">
                  <p className="text-[10px] font-black text-primary uppercase tracking-widest mb-1">Color</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">{getFieldValue(car, 'color', 'Color')}</p>
                </div>
                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-slate-800/50">
                  <p className="text-[10px] font-black text-primary uppercase tracking-widest mb-1">Location</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white flex items-center">
                    <MapPin className="w-4 h-4 mr-1 text-gray-400" />
                    {getFieldValue(car, 'location', 'Location')}
                  </p>
                </div>
                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-slate-800/50">
                  <p className="text-[10px] font-black text-primary uppercase tracking-widest mb-1">Posted On</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">{getFieldValue(car, 'posted_on', 'posted_on', 'Posted_On')}</p>
                </div>
                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-slate-800/50">
                  <p className="text-[10px] font-black text-primary uppercase tracking-widest mb-1">Last Updated</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">{getFieldValue(car, 'last_updated', 'last_updated', 'Last_Updated')}</p>
                </div>
              </div>
            </div>

            {/* Description */}
            {car.description && (
              <div className="bg-white dark:bg-slate-900 rounded-[2rem] p-8 border border-gray-100 dark:border-slate-800">
                <h2 className="text-2xl font-black text-gray-900 dark:text-white tracking-tight mb-6">Description</h2>
                <p className="text-gray-600 dark:text-slate-400 leading-relaxed whitespace-pre-line">
                  {car.description}
                </p>
              </div>
            )}

            {/* Source URL */}
            {car.url && (
              <div className="bg-white dark:bg-slate-900 rounded-[2rem] p-8 border border-gray-100 dark:border-slate-800">
                <h2 className="text-2xl font-black text-gray-900 dark:text-white tracking-tight mb-4">Source</h2>
                <a 
                  href={car.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-primary hover:underline font-medium break-all"
                >
                  {car.url}
                </a>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Contact Card */}
            <div className="bg-white dark:bg-slate-900 rounded-[2rem] p-8 border border-gray-100 dark:border-slate-800 sticky top-6">
              <h3 className="text-xl font-black text-gray-900 dark:text-white tracking-tight mb-6">Contact Seller</h3>
              
              <div className="space-y-4">
                <button className="w-full py-4 px-6 rounded-2xl ai-gradient text-white text-lg font-black shadow-xl shadow-primary/20 hover:shadow-primary/40 transition-all flex items-center justify-center space-x-3">
                  <MessageCircle className="w-5 h-5" />
                  <span>Send Message</span>
                </button>
                
                <button className="w-full py-4 px-6 rounded-2xl bg-white dark:bg-slate-800 border-2 border-gray-100 dark:border-slate-700 text-lg font-black text-gray-900 dark:text-white hover:border-primary transition-all">
                  Call Seller
                </button>
              </div>

              {/* Trust Badges */}
              <div className="mt-8 pt-6 border-t border-gray-100 dark:border-slate-800">
                <div className="flex items-center space-x-3 text-gray-500 dark:text-slate-400">
                  <ShieldCheck className="w-5 h-5 text-green-500" />
                  <span className="text-sm font-medium">Verified Seller</span>
                </div>
              </div>
            </div>

            {/* Similar Cars Placeholder */}
            <div className="bg-white dark:bg-slate-900 rounded-[2rem] p-8 border border-gray-100 dark:border-slate-800">
              <h3 className="text-xl font-black text-gray-900 dark:text-white tracking-tight mb-4">Similar Cars</h3>
              <p className="text-gray-500 dark:text-slate-400 text-sm">Check out more cars like this one!</p>
              <Link 
                to="/"
                className="inline-block mt-4 text-primary font-black text-sm hover:underline"
              >
                Browse Marketplace →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CarDetails;