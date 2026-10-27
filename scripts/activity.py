"""Fetch public/shared anonymous contribution counts and render a standalone contribution calendar SVG."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape
import json
import os
import re

QUERY = '''query($login:String!, $from:DateTime!, $to:DateTime!) {
 user(login:$login) { login contributionsCollection(from:$from,to:$to) {
 startedAt endedAt hasAnyRestrictedContributions restrictedContributionsCount
 contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
 } }
}'''


def fetch(login: str, now: datetime) -> dict:
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if not token:
        raise ValueError('GITHUB_TOKEN ou GH_TOKEN requis pour lire GraphQL.')
    start = now.date() - timedelta(days=364)
    variables = {'login': login, 'from': f'{start}T00:00:00Z', 'to': now.isoformat().replace('+00:00', 'Z')}
    request = Request('https://api.github.com/graphql',
                      data=json.dumps({'query': QUERY, 'variables': variables}).encode(),
                      headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
                               'User-Agent': 'SouphianeJ-profile-activity'})
    try:
        with urlopen(request, timeout=45) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise ValueError(f'GitHub GraphQL : HTTP {error.code}. Graphiques précédents conservés.') from None
    except (URLError, TimeoutError, json.JSONDecodeError):
        raise ValueError('Réponse GitHub indisponible ou invalide. Graphiques précédents conservés.') from None
    if payload.get('errors'):
        raise ValueError('GitHub a refusé la requête GraphQL. Graphiques précédents conservés.')
    user = (payload.get('data') or {}).get('user')
    if not user or user.get('login', '').lower() != login.lower():
        raise ValueError('Profil GitHub introuvable dans la réponse.')
    return {'user': login, 'source': 'GitHub GraphQL API',
            'fetched_at': now.isoformat().replace('+00:00', 'Z'), 'collection': user['contributionsCollection']}


def validate(data: dict) -> tuple[date, date, dict[date, int]]:
    try:
        c = data['collection']; calendar = c['contributionCalendar']
        start = date.fromisoformat(c['startedAt'][:10]); end = date.fromisoformat(c['endedAt'][:10])
        if (end - start).days != 364:
            raise ValueError('La fenêtre doit couvrir exactement 365 dates.')
        days = {}
        for week in calendar['weeks']:
            for entry in week['contributionDays']:
                day = date.fromisoformat(entry['date'])
                if not start <= day <= end:
                    continue
                count = entry['contributionCount']
                if day in days or type(count) is not int or count < 0:
                    raise ValueError('Dates dupliquées ou compteurs invalides.')
                days[day] = count
        total = calendar['totalContributions']; restricted = c['restrictedContributionsCount']
        if len(days) != 365 or sum(days.values()) != total:
            raise ValueError('Calendrier incomplet ou total incohérent.')
        if type(total) is not int or type(restricted) is not int or not 0 <= restricted <= total:
            raise ValueError('Totaux invalides.')
        if type(c['hasAnyRestrictedContributions']) is not bool:
            raise ValueError('Indicateur de contributions anonymisées absent.')
        return start, end, dict(sorted(days.items()))
    except (KeyError, TypeError, IndexError):
        raise ValueError('Schéma de contributions incomplet.') from None


def text(x, y, value, size=14, color='#0a0a0a', bold=False):
    return (f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" '
            f'font-weight="{700 if bold else 400}" fill="{color}">{escape(str(value))}</text>')


def number(n):
    return f'{n:,}'.replace(',', ' ')


def frame(title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="390" viewBox="0 0 1000 390" '
            f'role="img" aria-labelledby="title"><title id="title">{escape(title)}</title>'
            '<rect width="1000" height="390" fill="#f1efe7"/>'
            '<rect x="29" y="25" width="944" height="342" fill="#0a0a0a"/>'
            '<rect x="23" y="19" width="944" height="342" fill="#fffdf5" stroke="#0a0a0a" stroke-width="3"/>')


def footer(data, start, end):
    shared = data['collection']['restrictedContributionsCount'] > 0
    note = ('Contributions privées partagées anonymement incluses.' if shared
            else 'Activité visible au jeton de lecture ; aucun détail de dépôt publié.')
    return (text(44, 316, f'{start:%d/%m/%Y} → {end:%d/%m/%Y}', 12, bold=True)
            + text(44, 337, note, 12, '#5c5750')
            + text(44, 353, 'Source : GitHub GraphQL · Relevé UTC : ' + data['fetched_at'], 10, '#5c5750'))


def render(data):
    start, end, days = validate(data)
    c = data['collection']; total = c['contributionCalendar']['totalContributions']
    weekstart = start - timedelta(days=(start.weekday() + 1) % 7)
    colors = ['#e7e3d8', '#b7eeee', '#62dce6', '#00c4db', '#0a0a0a']
    maximum = max(days.values()); cuts = [max(1, maximum * .1), max(2, maximum * .3), max(3, maximum * .6)]
    calendar = [frame('Activité GitHub de ' + data['user']), text(44, 48, 'ACTIVITÉ GITHUB', 15, bold=True)]
    for x, count, label in [(44, total, 'contributions'), (349, sum(v > 0 for v in days.values()), 'jours avec contribution'),
                            (655, c['restrictedContributionsCount'], 'contributions anonymisées')]:
        calendar.extend([text(x, 97, number(count), 34, bold=True), text(x, 120, label, 13, '#5c5750')])
    monthnames = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
    for day, count in days.items():
        col = (day - weekstart).days // 7; row = (day.weekday() + 1) % 7
        level = 0 if not count else 1 + sum(count > limit for limit in cuts)
        calendar.append(f'<rect x="{82 + col * 16}" y="{161 + row * 16}" width="13" height="13" fill="{colors[level]}">'
                        f'<title>{day} : {count} contributions</title></rect>')
        if day.day == 1:
            calendar.append(text(82 + col * 16, 149, monthnames[day.month - 1], 10, '#5c5750'))
    for label, row in [('Lun.', 1), ('Mer.', 3), ('Ven.', 5)]:
        calendar.append(text(44, 171 + row * 16, label, 10, '#5c5750'))
    calendar.append(text(737, 295, 'Moins', 10, '#5c5750'))
    for i, color in enumerate(colors):
        calendar.append(f'<rect x="{777 + i * 18}" y="284" width="13" height="13" fill="{color}"/>')
    calendar.extend([text(873, 295, 'Plus', 10, '#5c5750'), footer(data, start, end), '</svg>'])
    return {'activity.svg': ''.join(calendar)}


def publish_local(data, output):
    # Validate and render before touching existing artifacts. Workflow only commits
    # after this command succeeds; an API failure preserves the previous graphs.
    rendered = render(data)
    start, end, days = validate(data)
    safe = {'user': data['user'], 'source': 'GitHub GraphQL API', 'fetched_at': data['fetched_at'],
            'period': {'from': start.isoformat(), 'to': end.isoformat()},
            'total_contributions': sum(days.values()),
            'restricted_contributions': data['collection']['restrictedContributionsCount'],
            'days': [{'date': str(day), 'count': count} for day, count in days.items()]}
    rendered['activity.json'] = json.dumps(safe, ensure_ascii=False, indent=2) + '\n'
    output = Path(output)
    # Preserve the timestamp of identical data to avoid twice-daily bot commits
    # solely for a new observation time. Re-render anyway so template edits apply.
    try:
        previous = json.loads((output / 'activity.json').read_text())
        without_time = lambda value: {k: v for k, v in value.items() if k != 'fetched_at'}
        datetime.fromisoformat(previous['fetched_at'].replace('Z', '+00:00'))
        if without_time(previous) == without_time(safe):
            data = dict(data, fetched_at=previous['fetched_at'])
            safe['fetched_at'] = previous['fetched_at']
            rendered = render(data)
            rendered['activity.json'] = json.dumps(safe, ensure_ascii=False, indent=2) + '\n'
    except (OSError, ValueError, KeyError, TypeError):
        pass
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='.activity-', dir=output) as temporary:
        for name, contents in rendered.items():
            (Path(temporary) / name).write_text(contents, encoding='utf-8')
        for name in rendered:
            (Path(temporary) / name).replace(output / name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--login', default='SouphianeJ')
    parser.add_argument('--output', type=Path, default=Path('assets'))
    parser.add_argument('--input', type=Path, help='Réponse agrégée déjà enregistrée, pour validation hors réseau.')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9-]{1,39}', args.login):
        parser.error('Identifiant GitHub invalide.')
    try:
        data = json.loads(args.input.read_text()) if args.input else fetch(args.login, datetime.now(timezone.utc))
        if data['user'].lower() != args.login.lower():
            raise ValueError('Le relevé ne correspond pas au profil demandé.')
        publish_local(data, args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    print('Calendrier de contributions actualisé : ' + args.login)


if __name__ == '__main__':
    main()
