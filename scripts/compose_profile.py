"""Compose the approved Facet hero locally. Graph refresh does not rewrite this."""
from pathlib import Path
from xml.sax.saxutils import escape
import re
ROOT=Path(__file__).resolve().parents[1]

def text(x,y,value,size=16,bold=False,color='#0a0a0a',mono=False):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="{ "monospace" if mono else "Arial,Helvetica,sans-serif"}" font-size="{size}" font-weight="{800 if bold else 400}">{escape(value)}</text>'

scene=(ROOT/'assets/astronaut.svg').read_text()
scene=re.sub(r'<svg[^>]*>','<svg xmlns="http://www.w3.org/2000/svg" x="742" y="190" width="202" height="198" viewBox="0 0 93 91" shape-rendering="crispEdges">',scene,count=1)
static=(ROOT/'assets/astronaut-static.svg').read_text();static=static[static.index('<svg'):]
static=re.sub(r'<svg[^>]*>','<svg xmlns="http://www.w3.org/2000/svg" x="742" y="190" width="202" height="198" viewBox="0 0 93 91" shape-rendering="crispEdges">',static,count=1)
start='<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="574" viewBox="0 0 1000 574" role="img" aria-labelledby="title desc"><title id="title">Comprendre et collaborer pour concevoir des solutions faciles à adopter</title><desc id="desc">Souphiane Jender. Application métier, intégration de système et agents IA. Animation pixel art : matérialisation, chute du drapeau et dispersion commune.</desc><defs><pattern id="paper-grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#0a0a0a" stroke-opacity=".045"/></pattern></defs><rect width="1000" height="574" fill="#f1efe7"/>'
p=[start,'<rect x="32" y="24" width="936" height="44" fill="#0a0a0a"/>',text(48,53,'SJ / SOUPHIANE JENDER',18,True,'#fffdf5',True),text(662,52,'PÉDAGOGIE · DEV · IA',14,False,'#00e5ff',True),'<rect x="39" y="99" width="936" height="449" fill="#0a0a0a"/><rect x="32" y="92" width="936" height="449" fill="#fffdf5" stroke="#0a0a0a" stroke-width="3"/><rect x="32" y="92" width="936" height="449" fill="url(#paper-grid)"/><rect x="56" y="109" width="660" height="29" fill="#c6ff00" stroke="#0a0a0a" stroke-width="2"/>',text(67,129,'APPLICATION MÉTIER · INTÉGRATION DE SYSTÈME · AGENTS IA',11,True,mono=True),text(58,194,'COMPRENDRE',46,True),text(58,250,'ET COLLABORER',46,True,'#ff3b1f'),text(58,306,'POUR CONCEVOIR',46,True),text(58,362,'DES SOLUTIONS',46,True),'<rect x="56" y="385" width="660" height="62" fill="#00e5ff" stroke="#0a0a0a" stroke-width="3"/>',text(68,430,'FACILES À ADOPTER',43,True),'SCENE',text(60,502,'Avec les équipes, au quotidien.',22,True),'</svg>']
base=''.join(p)
(ROOT/'assets/hero.svg').write_text(base.replace('SCENE',scene))
(ROOT/'assets/hero-static.svg').write_text(base.replace('SCENE',static))
print('Bandeau Facet composé avec l’animation validée.')
