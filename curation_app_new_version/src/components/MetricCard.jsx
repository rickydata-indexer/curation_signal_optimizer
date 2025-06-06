import React from 'react';

export default function MetricCard({ 
  title, 
  value, 
  subtitle, 
  icon: Icon, 
  iconColor = "text-blue-600",
  trend,
  className = "" 
}) {
  return (
    <div className={`card-neumorphic p-6 ${className}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-neumorphic mb-1">{title}</p>
          <p className="text-3xl font-bold text-neumorphic-dark mb-2">{value}</p>
          {subtitle && (
            <p className="text-sm text-neumorphic">{subtitle}</p>
          )}
          {trend && (
            <div className="mt-3">
              <span className={`text-sm font-medium ${
                trend.isPositive ? 'text-emerald-600' : 'text-red-500'
              }`}>
                {trend.isPositive ? '↗' : '↘'} {trend.value}
              </span>
              <span className="text-xs text-neumorphic ml-2">{trend.label}</span>
            </div>
          )}
        </div>
        <div className="neumorphic-subtle rounded-2xl p-4 ml-4">
          <Icon className={`w-6 h-6 ${iconColor}`} />
        </div>
      </div>
    </div>
  );
}