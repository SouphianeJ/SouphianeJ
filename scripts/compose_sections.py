"""Render Facet-styled sections as SVG images supported by GitHub READMEs."""
from pathlib import Path
from xml.sax.saxutils import escape
import re,textwrap
ROOT=Path(__file__).resolve().parents[1]
INK='#0a0a0a';PAPER='#f1efe7';SURFACE='#fffdf5'
source=(ROOT/'content/profile.md').read_text()

def clean(s):return s.replace('**','').replace('`','')
def txt(x,y,s,size=22,bold=False,mono=False,color=INK):
 return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-family="{ "monospace" if mono else "Arial,Helvetica,sans-serif"}" font-weight="{700 if bold else 400}">{escape(s)}</text>'
def rect(x,y,w,h,fill,stroke=None):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="3"' if stroke else '')+'/>'
def wrap(block,width=82):
 return textwrap.wrap(clean(block),width=width,break_long_words=False,break_on_hyphens=False)
def section(name,title,blocks,accent='#c6ff00'):
 cursor=104;body=[]
 for block in blocks:
  if not block.strip():continue
  bold=block.startswith('**') and block.endswith('**')
  for line in wrap(block,78 if bold else 83):body.append(txt(58,cursor,line,22,bold=bold));cursor+=32
  cursor+=16
 height=cursor+32
 s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}" role="img"><title>{escape(title)}</title><desc>{escape(clean(" ".join(blocks)))}</desc>',rect(0,0,1000,height,PAPER),rect(39,23,936,height-46,INK),rect(32,16,936,height-46,SURFACE,INK),rect(32,16,936,48,accent,INK),txt(53,48,title,20,True,True),*body,'</svg>']
 (ROOT/'assets'/name).write_text(''.join(s))

# Split only on existing Markdown section boundaries; preserve all approved copy.
parts=re.split(r'^## (.+)\n',source,flags=re.M)
intro=[x.strip() for x in parts[0].split('\n\n') if x.strip()]
section('introduction.svg','INGÉNIEUR PÉDAGOGIQUE · CHEF DE PROJET · DÉVELOPPEUR',intro[1:])
entries=dict(zip(parts[1::2],parts[2::2]))
section('approach.svg','01 / CONCEVOIR AVEC LES ÉQUIPES',[x.strip() for x in entries['Concevoir avec les équipes'].strip().split('\n\n')])
project_parts=re.split(r'^### (.+)\n',entries['Projets phares'],flags=re.M)
projects=list(zip(project_parts[1::2],project_parts[2::2]));colors=['#00e5ff','#c6ff00','#ff4fc8','#00e5ff']
project_names=[]
for i,(title,content) in enumerate(projects):
 name=f'project-{i+1}.svg';project_names.append((name,title))
 # Full-width cards keep the longer iStage description readable on GitHub.
 section(name,f'{i+1:02} / '+title.upper(),[x.strip() for x in content.strip().split('\n\n')],colors[i])
section('workshop.svg','03 / AUSSI DANS L’ATELIER',[x[2:] if x.startswith('- ') else x for x in entries['Aussi dans l’atelier'].strip().splitlines()])
section('engineering.svg','04 / DU PROTOTYPE À UN OUTIL MAINTENABLE',[x.strip() for x in entries['Du prototype à un outil maintenable'].strip().split('\n\n')], '#00e5ff')
section('stack.svg','05 / ENVIRONNEMENT TECHNIQUE',['Langages : Python · TypeScript · PHP · SQL','Applications et données : Next.js · FastAPI · MongoDB','Intégration et agents : REST · SOAP · MCP · Microsoft Graph'])
footer=source.split('---')[-1].strip()
section('closing.svg','COMPRENDRE · CONCEVOIR · FAIRE ÉVOLUER',[footer])
header='''<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="assets/hero-static.svg">
  <img src="assets/hero.svg" width="100%" alt="Comprendre et collaborer pour concevoir des solutions faciles à adopter.">
</picture>

'''
images=[('introduction.svg','Ingénieur pédagogique, chef de projet et développeur : besoins, cadrage et prototypage.'),('approach.svg','Concevoir avec les équipes et itérer au quotidien.'),*project_names,('workshop.svg','Tuteur IA, données d’exercice et planification.'),('engineering.svg','Du prototype à un outil maintenable.'),('stack.svg','Langages, applications, données et intégrations.'),('activity.svg','Calendrier des contributions GitHub.'),('closing.svg','Comprendre les usages. Concevoir avec les équipes. Faire évoluer les outils.')]
readme=header+'\n\n'.join(f'![{alt}](assets/{name})' for name,alt in images)
text=re.sub(r'^!\[.*?\]\(.*?\)\s*','',source,flags=re.M)
readme+='\n\n<details>\n<summary>Lire la version texte</summary>\n\n'+text+'\n</details>\n'
(ROOT/'README.md').write_text(readme)
print('Sections Facet générées ; titre Markdown en doublon retiré ; texte intégral conservé.')
