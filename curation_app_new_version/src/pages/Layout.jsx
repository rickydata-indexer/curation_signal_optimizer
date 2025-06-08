
import React from "react";
import { Link, useLocation } from "react-router-dom";
import { createPageUrl } from "@/utils";
import { TrendingUp, Wallet, Search, List } from "lucide-react";

export default function Layout({ children, currentPageName }) {
  const location = useLocation();

  return (
    <div className="min-h-screen" style={{
      background: '#e0e0e0',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif'
    }}>
      <style>{`
        :root {
          --neumorphic-bg: #e0e0e0;
          --neumorphic-light: rgba(255, 255, 255, 0.7);
          --neumorphic-dark: rgba(0, 0, 0, 0.15);
        }
        
        .neumorphic {
          background: var(--neumorphic-bg);
          box-shadow: 
            8px 8px 16px var(--neumorphic-dark),
            -8px -8px 16px var(--neumorphic-light);
          border: none;
        }
        
        .neumorphic-inset {
          background: var(--neumorphic-bg);
          box-shadow: 
            inset 4px 4px 8px var(--neumorphic-dark),
            inset -4px -4px 8px var(--neumorphic-light);
          border: none;
        }
        
        .neumorphic-pressed {
          background: var(--neumorphic-bg);
          box-shadow: 
            inset 6px 6px 12px var(--neumorphic-dark),
            inset -6px -6px 12px var(--neumorphic-light);
          border: none;
          transform: translateY(1px);
        }
        
        .neumorphic-subtle {
          background: var(--neumorphic-bg);
          box-shadow: 
            4px 4px 8px var(--neumorphic-dark),
            -4px -4px 8px var(--neumorphic-light);
          border: none;
        }
        
        .text-neumorphic {
          color: #666;
          text-shadow: 1px 1px 2px var(--neumorphic-light);
        }
        
        .text-neumorphic-dark {
          color: #333;
          text-shadow: 1px 1px 2px var(--neumorphic-light);
        }
        
        .btn-neumorphic {
          background: var(--neumorphic-bg);
          box-shadow: 
            6px 6px 12px var(--neumorphic-dark),
            -6px -6px 12px var(--neumorphic-light);
          border: none;
          transition: all 0.2s ease;
        }
        
        .btn-neumorphic:hover {
          box-shadow: 
            8px 8px 16px var(--neumorphic-dark),
            -8px -8px 16px var(--neumorphic-light);
        }
        
        .btn-neumorphic:active {
          box-shadow: 
            inset 4px 4px 8px var(--neumorphic-dark),
            inset -4px -4px 8px var(--neumorphic-light);
          transform: translateY(1px);
        }
        
        .input-neumorphic {
          background: var(--neumorphic-bg);
          box-shadow: 
            inset 3px 3px 6px var(--neumorphic-dark),
            inset -3px -3px 6px var(--neumorphic-light);
          border: none;
          color: #333;
        }
        
        .input-neumorphic:focus {
          outline: none;
          box-shadow: 
            inset 4px 4px 8px var(--neumorphic-dark),
            inset -4px -4px 8px var(--neumorphic-light),
            0 0 0 2px rgba(59, 130, 246, 0.3);
        }
        
        .card-neumorphic {
          background: var(--neumorphic-bg);
          box-shadow: 
            12px 12px 24px var(--neumorphic-dark),
            -12px -12px 24px var(--neumorphic-light);
          border: none;
          border-radius: 20px;
        }
        
        .tab-active {
          background: var(--neumorphic-bg);
          box-shadow: 
            inset 4px 4px 8px var(--neumorphic-dark),
            inset -4px -4px 8px var(--neumorphic-light);
          color: #4f46e5;
        }
        
        .tab-inactive {
          background: var(--neumorphic-bg);
          box-shadow: 
            4px 4px 8px var(--neumorphic-dark),
            -4px -4px 8px var(--neumorphic-light);
          color: #666;
        }
        
        .tab-inactive:hover {
          box-shadow: 
            6px 6px 12px var(--neumorphic-dark),
            -6px -6px 12px var(--neumorphic-light);
        }
      `}</style>
      
      <header className="neumorphic p-6 mb-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-neumorphic-dark mb-2">
                Curation Signal Optimizer
              </h1>
              <p className="text-neumorphic">
                Maximize your APR through intelligent signal allocation - made by{' '}
                <a
                  href="https://x.com/rickydata42"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline transition-colors"
                >
                  rickydata
                </a>
              </p>
            </div>
            <div className="neumorphic-subtle rounded-full p-4">
              <TrendingUp className="w-8 h-8 text-emerald-600" />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6">
        {children}
      </main>
    </div>
  );
}
