import React from 'react';

export function Button({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  className = '', 
  ...props 
}) {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer';
  
  const variants = {
    primary: 'bg-orange-500 text-white hover:bg-orange-600 hover:shadow-xs active:scale-[0.98]',
    secondary: 'bg-slate-100 border border-slate-200 text-slate-800 hover:bg-slate-200 hover:text-slate-900 active:scale-[0.98]',
    outline: 'border border-slate-200 bg-white text-slate-700 hover:text-slate-900 hover:border-slate-300 shadow-xs',
    ghost: 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/60',
    accent: 'bg-orange-500 text-white hover:bg-orange-600 shadow-xs active:scale-[0.98]',
  };

  const sizes = {
    sm: 'text-xs px-2.5 py-1.5 rounded-md gap-1.5',
    md: 'text-xs sm:text-sm px-4 py-2 rounded-lg gap-2',
    lg: 'text-sm sm:text-base px-5 py-2.5 rounded-xl gap-2.5',
  };

  return (
    <button 
      className={`${baseStyles} ${variants[variant] || variants.primary} ${sizes[size] || sizes.md} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
