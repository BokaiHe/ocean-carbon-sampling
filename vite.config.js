import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import {cp} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const root=fileURLToPath(new URL('.',import.meta.url));
const licensed=path.join(root,'site/licensed/MosaicWaves.tsx');
const hasLicensed=existsSync(licensed)&&process.env.OMIT_LICENSED_MOSAIC!=='1';
const heroLicensed=path.join(root,'site/licensed/Hero9.tsx');
const hasHero=existsSync(heroLicensed)&&process.env.OMIT_LICENSED_HERO!=='1';
// Keep frozen URLs stable: existing charts fetch data/*.json and maps by name.
// Only the hero is React-owned; the scientific renderers remain separate islands.
export default defineConfig({
  root:path.join(root,'site'),
  base:'./',
  publicDir:false,
  define:{__HAS_LICENSED_MOSAIC__:JSON.stringify(hasLicensed)},
  resolve:{alias:{'@licensed/mosaic-waves':hasLicensed?licensed:path.join(root,'site/src/StaticMosaic.jsx'),'@licensed/hero-nine':hasHero?heroLicensed:path.join(root,'site/src/Hero.jsx')}},
  plugins:[react(),{
    name:'preserve-frozen-research-assets',
    apply:'build',
    async closeBundle(){
      for(const name of ['assets','data','vendor','app.js','globe.js','observations.js','.nojekyll']){
        await cp(path.join(root,'site',name),path.join(root,'dist',name),{recursive:true});
      }
    }
  }],
  build:{outDir:path.join(root,'dist'),emptyOutDir:true},
  server:{port:5173},
  preview:{port:4173}
});
