import React from "react";
import { ExternalLink, Star, TrendingDown, BadgeCheck } from "lucide-react";

const ProductCard = ({ product, platform }) => {
  const isAmazon = platform === "amazon";
  const discount = product.discount_percent;
  
  return (
    <div className="card hover:shadow-lg transition-all duration-300 group">
      <div className="relative">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.title}
            className="w-full h-48 object-contain bg-gray-50 rounded-lg mb-4"
            onError={(e) => { e.target.style.display = "none"; }}
          />
        ) : (
          <div className="w-full h-48 bg-gray-100 rounded-lg mb-4 flex items-center justify-center text-gray-400">
            No Image
          </div>
        )}
        
        {discount && discount > 0 && (
          <div className="absolute top-2 left-2 bg-danger-500 text-white text-xs font-bold px-2 py-1 rounded-full">
            -{discount}%
          </div>
        )}
        
        <div className={`absolute top-2 right-2 text-xs font-medium px-2 py-1 rounded-full ${
          isAmazon ? "bg-orange-100 text-orange-700" : "bg-blue-100 text-blue-700"
        }`}>
          {isAmazon ? "Amazon" : "Flipkart"}
        </div>
      </div>
      
      <h3 className="font-semibold text-gray-900 text-sm line-clamp-2 mb-2 group-hover:text-primary-600 transition-colors">
        {product.title}
      </h3>
      
      <div className="flex items-center gap-2 mb-2">
        {product.rating && (
          <div className="flex items-center gap-1 text-amber-500">
            <Star className="w-4 h-4 fill-current" />
            <span className="text-sm font-medium">{product.rating}</span>
          </div>
        )}
        {product.review_count > 0 && (
          <span className="text-xs text-gray-500">({product.review_count.toLocaleString()})</span>
        )}
      </div>
      
      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-lg font-bold text-gray-900">
          ₹{product.price?.toLocaleString() || "N/A"}
        </span>
        {product.original_price && (
          <span className="text-sm text-gray-400 line-through">
            ₹{product.original_price.toLocaleString()}
          </span>
        )}
      </div>
      
      <div className="flex items-center gap-2">
        {product.badge && (
          <span className="badge badge-success text-xs">{product.badge}</span>
        )}
        {product.is_prime && (
          <span className="badge badge-info text-xs flex items-center gap-1">
            <BadgeCheck className="w-3 h-3" /> Prime
          </span>
        )}
        {product.is_fassured && (
          <span className="badge badge-warning text-xs">F-Assured</span>
        )}
        {product.is_sponsored && (
          <span className="badge badge-danger text-xs">Sponsored</span>
        )}
      </div>
      
      {product.source_url && (
        <a
          href={product.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 flex items-center justify-center gap-2 text-sm text-primary-600 hover:text-primary-700 font-medium py-2 border border-primary-200 rounded-lg hover:bg-primary-50 transition-colors"
        >
          <ExternalLink className="w-4 h-4" />
          View on {isAmazon ? "Amazon" : "Flipkart"}
        </a>
      )}
    </div>
  );
};

export default ProductCard;
