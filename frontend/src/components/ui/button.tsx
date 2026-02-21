import React from 'react';
import { ArrowPathIcon } from '@/components/icons';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  fullWidth?: boolean;
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  disabled,
  className = '',
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

  const variantStyles = {
    primary:
      'bg-orange-500 text-white hover:bg-orange-600 focus:ring-orange-500 shadow-sm',
    secondary:
      'bg-secondary text-secondary-foreground hover:bg-secondary/80 focus:ring-ring',
    danger: 'bg-destructive text-white hover:bg-destructive/90 focus:ring-destructive shadow-sm',
    ghost: 'text-foreground hover:bg-accent hover:text-accent-foreground focus:ring-ring',
  };

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
    icon: 'text-sm',
  };

  const widthStyle = fullWidth ? 'w-full' : '';

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${widthStyle} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <ArrowPathIcon className="animate-spin -ml-1 mr-2 h-4 w-4" />}
      {children}
    </button>
  );
};
