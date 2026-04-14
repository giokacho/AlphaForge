import React from 'react';
import { theme } from '../styles/theme';

export default function Skeleton({ width = '100%', height = '20px', borderRadius = '8px', style = {} }) {
    return (
        <div 
           className="skeleton-pulse"
           style={{
            width, height, borderRadius,
            backgroundColor: theme.colors.background.secondary,
            ...style
        }} />
    );
}
