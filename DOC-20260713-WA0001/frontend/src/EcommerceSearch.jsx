import React, { useState } from "react";
import { useQuery } from "react-query";
import { Search, Filter, ShoppingCart, TrendingUp, Zap } from "lucide-react";
import ProductCard from "../components/ProductCard";
import PriceComparison from "../components/PriceComparison";
import { api } from "../utils/api";

const EcommerceSearch = () => {
  const [query, setQuery] = useState("");
  const [platform, setPlatform] = useState("all");
  const [sort, setSort] = useState("relevance");
  const [activeTab, setActiveTab] = useState("search");
  
  const { data: searchData, isLoading: searchLoading, refetch: searchRefetch } = useQuery(
    ["ecommerce-search", query, platform, sort],
    async () => {
      if (!query) return null;
      const results = [];
      if (platform === "all" || platform === "amazon") {
        const amazon = await api.get(`/ecommerce/amazon/search?q=${encodeURIComponent(query)}&sort=${sort}`);
        results.push(...(amazon.data.products || []).map(p => ({ ...p, _platform: "amazon" })));
      }
      if (platform === "all" || platform === "flipkart") {
        const flipkart = await api.get(`/ecommerce/flipkart/search?q=${encodeURIComponent(query)}&sort=${sort}`);
        results.push(...(flipkart.data.products || []).map(p => ({ ...p, _platform: "flipkart" })));
      }
      return results;
    },
    { enabled: false }
  );
  
  const { data: compareData, isLoading: compareLoading } = useQuery(
    ["ecommerce-compare", query],
    async () => {
      if (!query) return null;
      const res = await api.get(`/ecommerce/compare?q=${encodeURIComponent(query)}&limit=10`);
      return res.data;
    },
    { enabled: !!query && activeTab === "compare" }
  );
  
  const { data: amazonDeals } = useQuery(
    "amazon-deals",
    () => api.get("/ecommerce/amazon/deals?limit=20").then(r => r.data),
    { enabled: activeTab === "deals" }
  );
  
  const { data: flipkartDeals } = useQuery(
    "flipkart-deals",
    () => api.get("/ecommerce/flipkart/deals?limit=20").then(r => r.data),
    { enabled: activeTab === "deals" }
  );
  
  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      searchRefetch();
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <ShoppingCart className="w-6 h-6 text-primary-600" />
            E-Commerce Intelligence
          </h1>
          
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="flex gap-2 mb-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search products on Amazon & Flipkart..."
                className="input-field pl-10"
              />
            </div>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="input-field w-32"
            >
              <option value="all">All</option>
              <option value="amazon">Amazon</option>
              <option value="flipkart">Flipkart</option>
            </select>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="input-field w-40"
            >
              <option value="relevance">Relevance</option>
              <option value="price_low">Price: Low to High</option>
              <option value="price_high">Price: High to Low</option>
              <option value="rating">Top Rated</option>
            </select>
            <button type="submit" className="btn-primary">
              <Search className="w-4 h-4" /> Search
            </button>
          </form>
          
          {/* Tabs */}
          <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit">
            {["search", "compare", "deals", "bestsellers"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-md text-sm font-medium capitalize transition-all ${
                  activeTab === tab
                    ? "bg-white text-primary-600 shadow-sm"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {tab === "bestsellers" ? "Best Sellers" : tab}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Search Results */}
        {activeTab === "search" && (
          <>
            {searchLoading && (
              <div className="flex items-center justify-center py-20">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
              </div>
            )}
            
            {searchData && searchData.length > 0 ? (
              <>
                <div className="mb-4 flex items-center justify-between">
                  <p className="text-gray-600">{searchData.length} products found</p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {searchData.map((product, idx) => (
                    <ProductCard
                      key={`${product.source_id}-${idx}`}
                      product={product}
                      platform={product._platform || product.platform}
                    />
                  ))}
                </div>
              </>
            ) : searchData && searchData.length === 0 ? (
              <div className="text-center py-20">
                <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg">No products found</p>
                <p className="text-gray-400">Try a different search term</p>
              </div>
            ) : (
              <div className="text-center py-20">
                <ShoppingCart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg">Search for products</p>
                <p className="text-gray-400">Enter a product name to compare prices across Amazon and Flipkart</p>
              </div>
            )}
          </>
        )}
        
        {/* Price Comparison */}
        {activeTab === "compare" && compareData && (
          <>
            <PriceComparison data={compareData} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
                  <span className="w-3 h-3 bg-orange-500 rounded-full"></span> Amazon
                </h3>
                <div className="space-y-3">
                  {compareData.amazon.products.slice(0, 5).map((p, i) => (
                    <ProductCard key={i} product={p} platform="amazon" />
                  ))}
                </div>
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
                  <span className="w-3 h-3 bg-blue-500 rounded-full"></span> Flipkart
                </h3>
                <div className="space-y-3">
                  {compareData.flipkart.products.slice(0, 5).map((p, i) => (
                    <ProductCard key={i} product={p} platform="flipkart" />
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
        
        {/* Deals */}
        {activeTab === "deals" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-bold text-orange-600 mb-3 flex items-center gap-2">
                <Zap className="w-5 h-5" /> Amazon Deals
              </h3>
              <div className="space-y-3">
                {amazonDeals?.deals?.map((deal, i) => (
                  <div key={i} className="card flex items-center gap-4">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{deal.title}</p>
                      <p className="text-primary-600 font-bold">₹{deal.price?.toLocaleString()}</p>
                      {deal.discount_text && <span className="badge badge-danger text-xs">{deal.discount_text}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-lg font-bold text-blue-600 mb-3 flex items-center gap-2">
                <Zap className="w-5 h-5" /> Flipkart Deals
              </h3>
              <div className="space-y-3">
                {flipkartDeals?.deals?.map((deal, i) => (
                  <div key={i} className="card flex items-center gap-4">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{deal.title}</p>
                      <p className="text-primary-600 font-bold">₹{deal.price?.toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {/* Bestsellers */}
        {activeTab === "bestsellers" && (
          <div className="text-center py-20">
            <TrendingUp className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg">Best Sellers</p>
            <p className="text-gray-400">Coming soon - Browse top-selling products by category</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EcommerceSearch;
