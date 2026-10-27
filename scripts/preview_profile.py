"""Render a local review of the controlled README; no network or Javascript."""
from pathlib import Path
from html import escape
import re
ROOT=Path(__file__).resolve().parents[1]

def inline(value):
 value=escape(value)
 value=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',value)
 value=re.sub(r'`(.+?)`',r'<code>\1</code>',value)
 return value

lines=(ROOT/'README.md').read_text().splitlines();out=[];i=0
while i<len(lines):
 line=lines[i]
 if not line.strip():i+=1;continue
 if line.startswith('<picture>'):
  block=[]
  while i<len(lines):
   block.append(lines[i]);i+=1
   if block[-1]=='</picture>':break
  out.append('\n'.join(block));continue
 if line.startswith('#'):
  level=len(line)-len(line.lstrip('#'));out.append(f'<h{level}>'+inline(line[level:].strip())+f'</h{level}>');i+=1;continue
 if line=='---':out.append('<hr>');i+=1;continue
 if line.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].startswith('|'):
   row=[x.strip() for x in lines[i].strip('|').split('|')];i+=1
   if all(re.fullmatch(r'[- :]+',x) for x in row):continue
   tag='th' if not rows else 'td';rows.append('<tr>'+''.join(f'<{tag}>'+inline(x)+f'</{tag}>' for x in row)+'</tr>')
  out.append('<table>'+''.join(rows)+'</table>');continue
 if line.startswith('- '):
  rows=[]
  while i<len(lines) and lines[i].startswith('- '):rows.append('<li>'+inline(lines[i][2:])+'</li>');i+=1
  out.append('<ul>'+''.join(rows)+'</ul>');continue
 m=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',line)
 if m:out.append('<img src="'+escape(m[2],quote=True)+'" alt="'+escape(m[1],quote=True)+'">');i+=1;continue
 paragraph=[]
 while i<len(lines) and lines[i].strip():paragraph.append(lines[i]);i+=1
 out.append('<p>'+inline(' '.join(paragraph))+'</p>')
css='''*{box-sizing:border-box}body{margin:0;padding:28px 16px;background:#e7e3d8;color:#0a0a0a;font:17px/1.65 Arial,Helvetica,sans-serif}main{max-width:1000px;margin:auto;background:#fffdf5;padding:32px;border:2px solid #0a0a0a;box-shadow:6px 6px #0a0a0a}img{max-width:100%;display:block;height:auto}picture{display:block;margin:0 -16px 26px}h1{font-size:34px;line-height:1.2;margin:0 0 26px}h2{font-size:25px;line-height:1.3;margin:38px 0 18px;padding-bottom:8px;border-bottom:2px solid #0a0a0a}h3{font-size:20px;line-height:1.3;margin:26px 0 10px}p{margin:14px 0}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:2px solid #0a0a0a;padding:12px;text-align:left}th{background:#c6ff00}hr{border:0;border-top:2px solid #0a0a0a;margin-top:30px}li{margin:10px 0}code{font-family:monospace} @media(max-width:600px){body{padding:10px}main{padding:20px 16px;font-size:16px}h1{font-size:28px}h2{font-size:23px}table{font-size:12px}td,th{padding:7px}}'''
(ROOT/'preview.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Souphiane Jender — fiche complète</title><style>'+css+'</style><main>'+''.join(out)+'</main></html>')
