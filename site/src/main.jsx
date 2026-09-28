import React from 'react';
import {createRoot,hydrateRoot} from 'react-dom/client';
import Hero from '@licensed/hero-nine';
import MosaicBackdrop from './MosaicBackdrop.jsx';

hydrateRoot(document.getElementById('hero-root'),<Hero />);
document.querySelectorAll('[data-mosaic-background]').forEach(node=>createRoot(node).render(<MosaicBackdrop/>));
