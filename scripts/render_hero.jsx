import React from 'react';
import {renderToString} from 'react-dom/server';
import {readFile,writeFile} from 'node:fs/promises';
import Hero from '../site/src/Hero.jsx';

// Commit the prerendered HTML for readable content even before JS loads.
const target=new URL('../site/index.html',import.meta.url);
const html=await readFile(target,'utf8');
const start='<!-- react-hero:start -->',end='<!-- react-hero:end -->';
if(!html.includes(start)||!html.includes(end))throw Error('Hero boundary markers missing');
// Vite removes vite-ignore after preserving the stable poster URL. Otherwise it
// rewrites only the HTML poster URL, making the hydrated React props disagree.
const markup=renderToString(<Hero />).replace('<video ','<video vite-ignore ');
const rendered=`${start}\n<div id="hero-root">${markup}</div>\n${end}`;
await writeFile(target,html.slice(0,html.indexOf(start))+rendered+html.slice(html.indexOf(end)+end.length));
console.log('Prerendered React hero; frozen research sections unchanged.');
