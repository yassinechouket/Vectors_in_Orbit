"use client";

import Link from "next/link";
import { useUser } from "@/lib/UserContext";

export default function Header() {
  const { cartCount, isOnline } = useUser();

  return (
    <header className="header">
      <div className="header-inner">
        <Link href="/" className="logo">
          ✨ Matcha AI
        </Link>
        
        <div className="header-actions">
          <div 
            className={`status-indicator ${isOnline ? '' : 'offline'}`} 
            title={isOnline ? 'AI Connected' : 'Offline Mode'}
          />
          
          <button className="header-btn" title="Wishlist">
            ♡
          </button>
          
          <button className="header-btn" title="Cart">
            🛒
            {cartCount > 0 && <span className="badge">{cartCount}</span>}
          </button>
          
          <button className="header-btn" title="Account">
            👤
          </button>
        </div>
      </div>
    </header>
  );
}
