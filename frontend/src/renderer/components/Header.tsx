import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import { IconSun, IconMoon, IconSettings } from '@tabler/icons-react';

interface HeaderProps {
  activeWorkspace: string;
  onWorkspaceChange: (workspaceId: string) => void;
  onOpenSettings?: () => void;
}

const Header: React.FC<HeaderProps> = ({ activeWorkspace, onWorkspaceChange, onOpenSettings }) => {
  const { theme, toggleTheme } = useTheme();

  const workspaces = [
    { 
      id: 'chat', 
      label: 'Chat', 
      icon: 'M8 10h8M8 14h5M21 12c0 4.418-4.477 8-10 8a11.94 11.94 0 01-4-.7L3 20l.7-3.001A7.96 7.96 0 013 12c0-4.418 4.477-8 10-8s10 3.582 10 8z' 
    },
    { 
      id: 'dashboard', 
      label: 'Dashboard', 
      icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' 
    },
    { 
      id: 'agents', 
      label: 'AI Agents', 
      icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' 
    },
    { 
      id: 'code', 
      label: 'Code', 
      icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4' 
    },
    { 
      id: 'files', 
      label: 'Files', 
      icon: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z' 
    },
    { 
      id: 'planner', 
      label: 'Planner', 
      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' 
    },
    { 
      id: 'terminal', 
      label: 'Terminal', 
      icon: 'M8 9l4-4 4 4m0 6l-4 4-4-4' 
    },
    { 
      id: 'tools', 
      label: 'Tools', 
      icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065zM15 12a3 3 0 11-6 0 3 3 0 016 0z' 
    }
  ];

  return (
    <motion.header 
      className="flex items-center justify-between p-4 px-8 border-b border-[var(--border)] nav-glass transition-slide-down aurora-bg"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <motion.div 
        className="flex items-center gap-3"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        <motion.svg 
          className="w-8 h-8 text-gradient-aurora interactive-icon hover-spin shadow-glow-accent" 
          viewBox="0 0 24 24" 
          fill="none"
          whileHover={{ rotate: 360, scale: 1.1 }}
          transition={{ duration: 0.6 }}
        >
          <path 
            d="M12 2L2 7V17L12 22L22 17V7L12 2ZM5.472 8.25L12 12L18.528 8.25L12 4.5L5.472 8.25ZM4 16.349V9.125L11 12.924V20.149L4 16.349Z" 
            fill="currentColor"
          />
        </motion.svg>
        <motion.h1 
          className="text-xl font-bold text-aurora float-element"
          whileHover={{ scale: 1.05, x: 4 }}
          transition={{ duration: 0.2 }}
        >
          Nexus AI
        </motion.h1>
      </motion.div>

      <motion.nav 
        className="glass-card p-1.5 rounded-full flex items-center space-x-2 hover-lift interactive-card shadow-multi"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        {workspaces.map((workspace, index) => (
          <motion.button
            key={workspace.id}
            onClick={() => onWorkspaceChange(workspace.id)}
            className={`workspace-button flex items-center gap-2 px-4 py-2 rounded-full text-sm btn-haptic hover-lift-sm stagger-item ${
              activeWorkspace === workspace.id 
                ? 'active-workspace btn-gradient shadow-glow-accent' 
                : 'text-[var(--text-secondary)] glass-button hover-accent border-gradient-primary'
            }`}
            style={{ animationDelay: `${200 + index * 100}ms` }}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: 0.2 + index * 0.1 }}
            whileHover={{ scale: 1.05, backgroundColor: 'var(--bg-tertiary)' }}
            whileTap={{ scale: 0.95 }}
          >
            <motion.svg 
              className="w-5 h-5 interactive-icon text-gradient-primary" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              whileHover={{ rotate: 15, scale: 1.1 }}
              transition={{ duration: 0.2 }}
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={workspace.icon}></path>
            </motion.svg>
            <span>{workspace.label}</span>
          </motion.button>
        ))}
      </motion.nav>

      <motion.div 
        className="flex items-center gap-4"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3, delay: 0.2 }}
      >
        <motion.button 
          onClick={toggleTheme}
          className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors p-2 rounded-lg glass-button btn-elastic interactive-icon neon-border"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          whileHover={{ scale: 1.1, backgroundColor: 'var(--bg-secondary)' }}
          whileTap={{ scale: 0.9 }}
        >
          <AnimatePresence mode="wait">
            {theme === 'dark' ? (
              <motion.div
                key="sun"
                initial={{ opacity: 0, rotate: -90 }}
                animate={{ opacity: 1, rotate: 0 }}
                exit={{ opacity: 0, rotate: 90 }}
                transition={{ duration: 0.2 }}
                className="transition-scale-in neon-orange"
              >
                <IconSun className="w-6 h-6" />
              </motion.div>
            ) : (
              <motion.div
                key="moon"
                initial={{ opacity: 0, rotate: 90 }}
                animate={{ opacity: 1, rotate: 0 }}
                exit={{ opacity: 0, rotate: -90 }}
                transition={{ duration: 0.2 }}
                className="transition-scale-in neon-blue"
              >
                <IconMoon className="w-6 h-6" />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.button>
        
        <motion.button 
          className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors p-2 rounded-lg glass-button btn-elastic interactive-icon border-gradient-aurora"
          whileHover={{ scale: 1.1, rotate: 90, backgroundColor: 'var(--bg-secondary)' }}
          whileTap={{ scale: 0.9 }}
          onClick={() => onOpenSettings && onOpenSettings()}
        >
          <IconSettings className="w-6 h-6 text-gradient-cosmic" />
        </motion.button>
        
        <motion.img 
          src="https://placehold.co/40x40/7b5aff/f0f0f0?text=JD" 
          className="w-10 h-10 rounded-full cursor-pointer border-2 border-transparent hover:border-[var(--primary-color)] hover-lift interactive-card shadow-glow-accent neon-border" 
          alt="Profile"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          transition={{ duration: 0.2 }}
        />
      </motion.div>
    </motion.header>
  );
};

export default Header;
