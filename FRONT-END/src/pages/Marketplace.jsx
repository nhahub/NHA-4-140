import React, { useState, useEffect } from 'react';
import { Sparkles, ArrowRight, Zap, TrendingUp, ShieldCheck, Search, ChevronRight, Loader2 } from 'lucide-react';
import { brands as defaultBrands } from '../data/mockData';
import { BrandCard, CarCard } from '../components/CarCards';
import FilterPanel from '../components/FilterPanel';
import { fetchCars, fetchBrands } from '../api/carApi';
import { cn } from '../hooks/utils';

const Marketplace = () => {
  const [activeBrand, setActiveBrand] = useState('All');
  const [cars, setCars] = useState([]);
  const [brands, setBrands] = useState(defaultBrands);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCars();
    loadBrands();
  }, [page]);

  const loadCars = async () => {
    try {
      setLoading(true);
      const data = await fetchCars(page, 12);
      setCars(data.cars);
      setTotalPages(data.total_pages);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadBrands = async () => {
    try {
      const data = await fetchBrands();
      if (data.brands && data.brands.length > 0) {
        const formattedBrands = data.brands.map((brand, index) => ({
          id: brand.toLowerCase().replace(/\s/g, '_'),
          name: brand,
          logo: `https://placehold.co/100x100/png?text=${brand}`
        }));
        setBrands([{ id: 'all', name: 'All', logo: 'https://placehold.co/100x100/png?text=All' }, ...formattedBrands]);
      }
    } catch (err) {
      console.error('Failed to load brands:', err);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] dark:bg-slate-950 pb-24 transition-colors duration-300">
      {/* Hero Section */}
      <section className="relative h-[85vh] min-h-[700px] flex items-center justify-center overflow-hidden bg-white dark:bg-slate-900/50 px-4 border-b border-gray-100 dark:border-slate-800">
        {/* Animated Background Elements */}
        <div className="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 rounded-full blur-[120px] animate-pulse" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-500/10 rounded-full blur-[120px] animate-pulse delay-700" />
        </div>

        <div className="max-w-7xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center space-x-3 px-6 py-3 rounded-full bg-primary/5 border border-primary/10 text-primary text-sm font-black mb-10 shadow-sm backdrop-blur-sm">
            <Sparkles className="w-5 h-5" />
            <span className="tracking-[0.2em] uppercase text-[11px]">AI-POWERED MARKETPLACE</span>
          </div>
          
          <h1 className="text-7xl md:text-9xl font-black text-gray-900 dark:text-white mb-10 tracking-tighter leading-[0.85]">
            Find Your <span className="ai-text-gradient">Next Car</span> <br /> 
            with <span className="italic font-light">AI Precision</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-600 dark:text-slate-400 max-w-2xl mx-auto mb-14 font-medium leading-relaxed">
            The world's most advanced automotive marketplace. 
            AI-driven valuations, smart recommendations, and seamless buying.
          </p>
          
          <div className="flex flex-wrap justify-center gap-6">
            <button className="px-12 py-6 rounded-[2rem] ai-gradient text-white text-xl font-black shadow-2xl shadow-primary/30 hover:shadow-primary/50 hover:scale-105 active:scale-95 transition-all flex items-center space-x-4 group">
              <span>Explore Inventory</span>
              <ArrowRight className="w-6 h-6 transition-transform group-hover:translate-x-2" />
            </button>
            <button className="px-12 py-6 rounded-[2rem] bg-white dark:bg-slate-800 border-2 border-gray-100 dark:border-slate-700 text-xl font-black hover:bg-gray-50 dark:hover:bg-slate-700 transition-all flex items-center space-x-4 text-gray-900 dark:text-white shadow-xl shadow-gray-200/50 dark:shadow-none">
              <Zap className="w-6 h-6 text-primary" />
              <span>AI Insights</span>
            </button>
          </div>
        </div>

        {/* Decorative Image */}
        <div className="absolute inset-0 w-full h-full opacity-40 dark:opacity-20 pointer-events-none select-none overflow-hidden">
          <img 
            src="/src/images/background_1.jpg" 
            alt="Hero Background" 
            className="w-full h-full object-cover blur-[2px]"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/50 to-white dark:via-slate-950/50 dark:to-slate-950" />
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-24">
        {/* Brand Selection */}
        <div className="mb-32">
          <div className="flex items-end justify-between mb-12">
            <div>
              <div className="flex items-center space-x-2 text-primary font-black text-xs uppercase tracking-widest mb-3">
                <div className="w-8 h-[2px] bg-primary" />
                <span>Top Manufacturers</span>
              </div>
              <h2 className="text-5xl font-black text-gray-900 dark:text-white tracking-tighter">Browse by Brand</h2>
            </div>
            <button className="text-primary font-black text-sm flex items-center space-x-2 hover:translate-x-1 transition-transform group">
              <span>View All Brands</span>
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
          
          <div className="flex overflow-x-auto pb-10 space-x-8 scrollbar-hide -mx-4 px-4">
            <BrandCard 
              brand={{ name: 'All', logo: 'https://placehold.co/100x100/png?text=All' }} 
              isActive={activeBrand === 'All'}
              onClick={() => setActiveBrand('All')}
            />
            {brands.filter(b => b.name !== 'All').map((brand) => (
              <BrandCard 
                key={brand.id} 
                brand={brand} 
                isActive={activeBrand === brand.name}
                onClick={() => setActiveBrand(brand.name)}
              />
            ))}
          </div>
        </div>

        {/* Filters */}
        <div className="mb-32">
          <FilterPanel />
        </div>

        {/* Car Grid */}
        <div className="flex items-end justify-between mb-12">
          <div>
            <div className="flex items-center space-x-2 text-primary font-black text-xs uppercase tracking-widest mb-3">
              <div className="w-8 h-[2px] bg-primary" />
              <span>Curated for You</span>
            </div>
            <h2 className="text-5xl font-black text-gray-900 dark:text-white tracking-tighter">Featured Listings</h2>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 bg-white dark:bg-slate-900 border-2 border-gray-100 dark:border-slate-800 p-2 rounded-2xl shadow-sm">
              <button className="px-6 py-2.5 rounded-xl bg-primary text-white text-xs font-black shadow-lg shadow-primary/20 transition-all">Grid</button>
              <button className="px-6 py-2.5 rounded-xl text-gray-400 dark:text-slate-500 text-xs font-black hover:text-primary transition-colors">List</button>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-10 h-10 text-primary animate-spin" />
          </div>
        ) : error ? (
          <div className="text-center py-20 text-red-500">
            <p>Error: {error}</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-12">
              {cars.map((car) => (
                <div key={car.id} className="animate-in fade-in slide-in-from-bottom-8 duration-700">
                  <CarCard car={car} />
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center items-center space-x-2 mt-12">
                <button 
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 rounded-xl bg-white dark:bg-slate-900 border-2 border-gray-100 dark:border-slate-800 disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="px-4 py-2 text-gray-600 dark:text-slate-400">
                  Page {page} of {totalPages}
                </span>
                <button 
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 rounded-xl bg-white dark:bg-slate-900 border-2 border-gray-100 dark:border-slate-800 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}

        {/* Stats Section */}
        <section className="mt-32 p-12 rounded-[3rem] glass border border-white/20 dark:border-slate-800/20 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/2" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 text-center relative z-10">
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-[1.5rem] bg-primary/10 flex items-center justify-center mx-auto text-primary">
                <TrendingUp className="w-8 h-8" />
              </div>
              <h3 className="text-4xl font-black text-foreground">15k+</h3>
              <p className="text-muted-foreground font-bold uppercase tracking-widest text-xs">AI Valuations Daily</p>
            </div>
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-[1.5rem] bg-indigo-500/10 flex items-center justify-center mx-auto text-indigo-500">
                <ShieldCheck className="w-8 h-8" />
              </div>
              <h3 className="text-4xl font-black text-foreground">100%</h3>
              <p className="text-muted-foreground font-bold uppercase tracking-widest text-xs">Verified Sellers</p>
            </div>
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-[1.5rem] bg-violet-500/10 flex items-center justify-center mx-auto text-violet-500">
                <Search className="w-8 h-8" />
              </div>
              <h3 className="text-4xl font-black text-foreground">0.5s</h3>
              <p className="text-muted-foreground font-bold uppercase tracking-widest text-xs">Avg. Search Time</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Marketplace;