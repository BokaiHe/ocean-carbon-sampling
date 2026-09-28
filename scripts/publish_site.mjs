// Publish application output, not the privately licensed component source.
// Run via npm run publish:site from the project with its licensed file installed.
import {cpSync,existsSync,mkdirSync,mkdtempSync,readdirSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';

const root=fileURLToPath(new URL('..',import.meta.url));
const licensed=path.join(root,'site/licensed/MosaicWaves.tsx');
if(!existsSync(licensed))throw Error('Local licensed MosaicWaves.tsx is required to publish. Public clones can still build the static fallback.');
if(!process.env.npm_execpath)throw Error('Use npm run publish:site.');
const repoGit=(...args)=>execFileSync('git',['-c',`safe.directory=${root.replaceAll('\\','/')}`,'-C',root,...args],{encoding:'utf8'}).trim();
const remote=repoGit('remote','get-url','origin');
if(!/^https:\/\/github\.com\/BokaiHe\/ocean-carbon-sampling(?:\.git)?$/i.test(remote))throw Error('Unexpected deployment remote; stopping.');
execFileSync(process.execPath,[process.env.npm_execpath,'run','build'],{cwd:root,stdio:'inherit'});
const dist=path.join(root,'dist');
const files=readdirSync(dist,{recursive:true}).map(String);
if(files.some(p=>/\.(tsx?|jsx|map)$/i.test(p)||p.split(/[\\/]/).includes('licensed')))throw Error('Source files must not enter the deployment artifact.');
const html=readFileSync(path.join(dist,'index.html'),'utf8');
if(!html.includes('data-mosaic-background'))throw Error('Build is missing the Mosaic section.');
const stage=mkdtempSync(path.join(tmpdir(),'ocean-site-publish-'));
cpSync(dist,stage,{recursive:true});
mkdirSync(path.join(stage,'.github/workflows'),{recursive:true});
cpSync(path.join(root,'.github/workflows/deploy-pages.yml'),path.join(stage,'.github/workflows/deploy-pages.yml'));
const identity={...process.env,GIT_AUTHOR_NAME:repoGit('config','user.name'),GIT_AUTHOR_EMAIL:repoGit('config','user.email'),GIT_COMMITTER_NAME:repoGit('config','user.name'),GIT_COMMITTER_EMAIL:repoGit('config','user.email')};
const git=(...args)=>execFileSync('git',['-C',stage,...args],{encoding:'utf8',env:identity}).trim();
git('init','--initial-branch=site-build');git('remote','add','origin',remote);
const existing=git('ls-remote','--heads','origin','site-build');
const parents=[];
if(existing){git('fetch','--depth=1','origin','site-build');parents.push('-p','FETCH_HEAD');}
git('add','--all');
const tree=git('write-tree');
const commit=git('commit-tree',tree,...parents,'-m',`Publish research site from ${repoGit('rev-parse','--short','HEAD')}`);
git('update-ref','refs/heads/site-build',commit);
git('push','origin','site-build:site-build');
console.log(`Published compiled website ${commit}. No licensed source or source maps uploaded. Deployment staging: ${stage}`);
