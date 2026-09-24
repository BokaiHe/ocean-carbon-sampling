import React from 'react';
import {hydrateRoot} from 'react-dom/client';
import Hero from './Hero.jsx';

hydrateRoot(document.getElementById('hero-root'),<Hero />);
