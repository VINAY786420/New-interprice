import React from "react";
import { ArrowRight, TrendingDown, TrendingUp, Minus } from "lucide-react";

const PriceComparison = ({ data }) => {
  if (!data) return null;
  
  const { amazon, flipkart, price_difference, cheaper_platform } = data;
  const diff = Math.abs(price_difference);
  
  return (
    <div className="card mb-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
        Price Comparison
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Amazon */}
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">A</div>
            <span className="font-semibold text-orange-800">Amazon</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">₹{amazon.avg_price.toLocaleString()}</div>
          <div className="text-sm text-gray-500">{amazon.total} products found</div>
        </div>
        
        {/* Difference */}
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 flex flex-col items-center justify-center">
          <div className="text-sm text-gray-500 mb-1">Difference</div>
          <div className={`text-2xl font-bold flex items-center gap-1 ${
            price_difference > 0 ? "text-green-600" : price_difference < 0 ? "text-red-600" : "text-gray-600"
          }`}>
            {price_difference > 0 ? <TrendingDown className="w-5 h-5" /> : 
             price_difference < 0 ? <TrendingUp className="w-5 h-5" /> : <Minus className="w-5 h-5" />}
            ₹{diff.toLocaleString()}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {cheaper_platform === "same" ? "Same price" : `${cheaper_platform} is cheaper`}
          </div>
        </div>
        
        {/* Flipkart */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">F</div>
            <span className="font-semibold text-blue-800">Flipkart</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">₹{flipkart.avg_price.toLocaleString()}</div>
          <div className="text-sm text-gray-500">{flipkart.total} products found</div>
        </div>
      </div>
    </div>
  );
};

export default PriceComparison;
