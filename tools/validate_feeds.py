#!/usr/bin/env python3
"""Read-only acceptance of the fixed PlannerSport V1.0 production profile.

No-argument CLI remains supported. Laboratory feeds are deliberately outside
this production result. UTC timestamps may differ between feed generations.
The parser accepts the generator's restricted ICS profile, not arbitrary RFC ICS.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from common import fingerprint, fmt_ics_utc, slugify, uid_for
from feed_builder import esc, event_lines, fold_line

ROOT = Path(__file__).resolve().parents[1]
# Explicit NBA team-name/tricode contract; never infer a tricode from a name.
TEAMS = {
    'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN',
    'Charlotte Hornets': 'CHA', 'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN', 'Detroit Pistons': 'DET',
    'Golden State Warriors': 'GSW', 'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
    'Los Angeles Clippers': 'LAC', 'Los Angeles Lakers': 'LAL',
    'Memphis Grizzlies': 'MEM', 'Miami Heat': 'MIA', 'Milwaukee Bucks': 'MIL',
    'Minnesota Timberwolves': 'MIN', 'New Orleans Pelicans': 'NOP',
    'New York Knicks': 'NYK', 'Oklahoma City Thunder': 'OKC', 'Orlando Magic': 'ORL',
    'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHX', 'Portland Trail Blazers': 'POR',
    'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SAS', 'Toronto Raptors': 'TOR',
    'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS',
}


class Invalid(ValueError):
    def __init__(self, code, detail=''):
        self.code, self.detail = code, detail
        super().__init__(code + (': ' + detail if detail else ''))


def require(ok, code, detail=''):
    if not ok:
        raise Invalid(code, detail)


def strict_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'JSON_DUPLICATE_KEY', key)
            result[key] = value
        return result

    def constant(value):
        raise Invalid('JSON_NONFINITE', value)

    try:
        data = json.loads(Path(path).read_bytes().decode('utf-8'),
                          object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Invalid('JSON_INVALID') from exc
    require(isinstance(data, dict), 'JSON_OBJECT_REQUIRED')
    return data


def utc(value, iso=False):
    pattern = r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z' if iso else r'[0-9]{8}T[0-9]{6}Z'
    require(isinstance(value, str) and re.fullmatch(pattern, value), 'UTC_INVALID')
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ' if iso else '%Y%m%dT%H%M%SZ')
    except ValueError as exc:
        raise Invalid('UTC_INVALID') from exc


def validate_inputs(master, state, identity):
    require(master.get('season') == state.get('season') == identity.get('season') == '2026-27', 'SEASON_MISMATCH')
    require(state.get('schema_version') == '3.3.0' and identity.get('schema_version') == '1.0.0', 'SCHEMA_UNSUPPORTED')
    events = master.get('events')
    require(isinstance(events, list) and len(events) == 1200, 'MASTER_COVERAGE')
    indexed, counts = {}, Counter()
    for e in events:
        require(isinstance(e, dict), 'MASTER_EVENT_INVALID')
        eid = e.get('ID_Partido')
        require(isinstance(eid, str) and re.fullmatch(r'NBA2627-[0-9]{4}', eid), 'MASTER_ID_INVALID')
        require(eid not in indexed, 'MASTER_ID_DUPLICATE', eid)
        for field in ('Visitante', 'Local'):
            require(isinstance(e.get(field), str) and e[field] in TEAMS, 'TEAM_INVALID', eid)
            counts[e[field]] += 1
        require(e['Visitante'] != e['Local'], 'TEAM_SAME', eid)
        require(e.get('Temporada') == '2026-27', 'SEASON_MISMATCH', eid)
        require(e.get('Estado') == 'Programado', 'STATUS_UNSUPPORTED', eid)
        utc(e.get('Fecha_Hora_UTC'), True)
        for flag in ('Es_NBA_Cup', 'Es_Partido_Especial'):
            require(type(e.get(flag)) is bool, 'CLASSIFICATION_INVALID', eid)
        for field in ('Arena', 'Ciudad', 'Estado_Provincia', 'País', 'Fase',
                      'TV_Normalizada', 'Streaming_Normalizado', 'Grupo_NBA_Cup',
                      'Evento_Especial', 'Zona_Horaria_Arena', 'URL_NBA'):
            require(field in e and (e[field] is None or isinstance(e[field], str)), 'MASTER_FIELD_INVALID', eid + '/' + field)
            require(e[field] is None or not any(c in e[field] for c in ('\r', '\x00')), 'MASTER_TEXT_INVALID', eid)
        indexed[eid] = e
    require(set(counts) == set(TEAMS) and all(n == 80 for n in counts.values()), 'TEAM_COVERAGE')
    require(sum(e['Es_NBA_Cup'] for e in events) == 60, 'CUP_COVERAGE')
    require(sum(e['Es_Partido_Especial'] for e in events) == 32, 'SPECIAL_COVERAGE')
    records = state.get('events')
    require(isinstance(records, dict) and set(records) == set(indexed), 'STATE_IDS_MISMATCH')
    for eid in sorted(indexed):
        record = records[eid]
        require(isinstance(record, dict), 'STATE_RECORD_INVALID', eid)
        require(record.get('uid') == uid_for(eid), 'STATE_UID_MISMATCH', eid)
        require(type(record.get('sequence')) is int and record['sequence'] >= 0, 'STATE_SEQUENCE_INVALID', eid)
        require(record.get('status') == 'ACTIVE', 'STATUS_UNSUPPORTED', eid)
        require(record.get('fingerprint') == fingerprint(indexed[eid]), 'STATE_FINGERPRINT_MISMATCH', eid)
        require('last_modified' in record, 'STATE_LAST_MODIFIED_MISSING', eid)
        if record['last_modified'] is not None:
            utc(record['last_modified'])
    relations = identity.get('events')
    require(isinstance(relations, list) and len(relations) == 1200, 'IDENTITY_COVERAGE')
    seen_ids, seen_games = set(), set()
    for relation in relations:
        require(isinstance(relation, dict), 'IDENTITY_INVALID')
        eid, gid = relation.get('ID_Partido'), relation.get('gameId')
        require(isinstance(eid, str) and eid in indexed and eid not in seen_ids, 'IDENTITY_ID_INVALID')
        require(isinstance(gid, str) and re.fullmatch(r'00226[0-9]{5}', gid) and gid not in seen_games, 'IDENTITY_GAME_INVALID', eid)
        e = indexed[eid]
        require(relation.get('Visitante_Tricode') == TEAMS[e['Visitante']] and
                relation.get('Local_Tricode') == TEAMS[e['Local']], 'IDENTITY_TEAM_MISMATCH', eid)
        # Historical matching date is valid evidence, not the current schedule.
        utc(relation.get('Fecha_Hora_UTC_Validacion'), True)
        seen_ids.add(eid); seen_games.add(gid)
    require(seen_ids == set(indexed), 'IDENTITY_COVERAGE')
    return indexed, records


def catalog(events):
    result = {
        'nba-2026-27-completo.ics': ('NBA 2026-27 — Completo', events),
        'nba-2026-27-cup-group-play.ics': ('NBA Cup 2026 — Group Play', [e for e in events if e['Es_NBA_Cup']]),
        'nba-2026-27-eventos-especiales.ics': ('NBA 2026-27 — Eventos especiales', [e for e in events if e['Es_Partido_Especial']]),
    }
    for team in sorted(TEAMS):
        result['teams/' + slugify(team) + '.ics'] = ('NBA 2026-27 — ' + team,
            [e for e in events if team in (e['Visitante'], e['Local'])])
    return result


def parse_calendar(raw, *, warnings=None, filename="<memory>", strict_folding=False):
    """Adapted from the pure restricted-profile parser in update_transaction."""
    require(raw.endswith(b'\r\n') and b'\r' not in raw.replace(b'\r\n', b'') and
            b'\n' not in raw.replace(b'\r\n', b''), 'ICS_CRLF')
    physical = raw.split(b'\r\n')[:-1]
    require(all(physical), 'ICS_EMPTY_LINE')
    if strict_folding:
        require(all(len(line) <= 75 for line in physical), 'ICS_FOLDING')
    try:
        physical = [line.decode('utf-8') for line in physical]
    except UnicodeError as exc:
        raise Invalid('ICS_UTF8') from exc
    lines = []
    owner = ''
    for number, line in enumerate(physical, 1):
        if not line.startswith((' ', '\t')):
            owner = line.split(':', 1)[0]
        if len(line.encode('utf-8')) > 75 and warnings is not None:
            warnings.append({'code': 'ICS_LINE_LENGTH_WARNING', 'file': filename,
                             'line': number, 'octets': len(line.encode('utf-8')), 'property': owner})
        require(not any(ord(c) < 32 and c != '\t' for c in line), 'ICS_CONTROL_CHARACTER')
        if line.startswith((' ', '\t')):
            require(bool(lines), 'ICS_CONTINUATION')
            lines[-1] += line[1:]
        else:
            lines.append(line)
    require(lines and lines[0] == 'BEGIN:VCALENDAR' and lines[-1] == 'END:VCALENDAR', 'ICS_ENVELOPE')
    require(lines.count('BEGIN:VCALENDAR') == lines.count('END:VCALENDAR') == 1, 'ICS_ENVELOPE')
    stack, events, header = [], [], {}
    for line in lines:
        require(':' in line, 'ICS_PROPERTY_INVALID')
        key, value = line.split(':', 1)
        require(re.fullmatch(r'[A-Z][A-Z0-9-]*', key) is not None, 'ICS_PROPERTY_UNSUPPORTED')
        if key == 'BEGIN':
            require((not stack and value == 'VCALENDAR') or
                    (stack == ['VCALENDAR'] and value == 'VEVENT') or
                    (stack == ['VCALENDAR', 'VEVENT'] and value == 'VALARM'), 'ICS_NESTING')
            stack.append(value)
            if value == 'VEVENT': events.append({'properties': {}, 'alarms': []})
            if value == 'VALARM': events[-1]['alarms'].append({})
        elif key == 'END':
            require(bool(stack) and stack.pop() == value, 'ICS_NESTING')
        else:
            require(bool(stack), 'ICS_NESTING')
            target = header if len(stack) == 1 else (events[-1]['properties'] if len(stack) == 2 else events[-1]['alarms'][-1])
            require(key not in target, 'ICS_PROPERTY_DUPLICATE', key)
            target[key] = value
    require(not stack, 'ICS_NESTING')
    return header, events


def cup_description(description, event, warnings=None, filename="<memory>"):
    """Normalize only one whole, recognized group declaration in memory.

    Split iCalendar escaped newlines without confusing an escaped backslash
    followed by 'n' with a newline. Preserve every other byte of DESCRIPTION.
    """
    require(isinstance(description, str), 'DESCRIPTION_REQUIRED', event['ID_Partido'])
    lines, current, pos = [], '', 0
    while pos < len(description):
        char = description[pos]
        if char == "\\" and pos + 1 < len(description):
            pair = description[pos:pos+2]
            if pair == "\\n":
                lines.append(current)
                current = ''
            else:
                current += pair
            pos += 2
        else:
            current += char
            pos += 1
    lines.append(current)
    declarations = [i for i, line in enumerate(lines)
                    if line.startswith(('Emirates NBA Cup', 'Grupo NBA Cup'))]
    eid = event['ID_Partido']
    if event['Es_NBA_Cup'] is not True:
        require(not declarations, 'CUP_DECLARATION_UNEXPECTED', eid)
        return description
    group = event.get('Grupo_NBA_Cup')
    require(isinstance(group, str) and bool(group.strip()), 'CUP_MASTER_GROUP_REQUIRED', eid)
    require(len(declarations) == 1, 'CUP_DECLARATION_COUNT', eid)
    index = declarations[0]
    actual = lines[index]
    canonical = 'Grupo NBA Cup: ' + esc(group)
    historical = 'Emirates NBA Cup — ' + esc(group)
    require(actual in (canonical, historical), 'CUP_GROUP_MISMATCH', eid)
    if actual == historical:
        lines[index] = canonical
        if warnings is not None:
            warnings.append({'code': 'ICS_HISTORICAL_CUP_DESCRIPTION_WARNING',
                             'file': filename, 'uid': uid_for(eid), 'group': group})
    return "\\n".join(lines)


def normalized(item, event, warnings=None, filename="<memory>"):
    # Alarm order is immaterial. DTSTAMP reflects feed generation, not identity.
    properties = {k: v for k, v in item['properties'].items() if k != 'DTSTAMP'}
    properties['DESCRIPTION'] = cup_description(properties.get('DESCRIPTION'), event,
                                                warnings, filename)
    return (properties, sorted(tuple(sorted(a.items())) for a in item['alarms']))


def validate_header(header, title, warnings=None, filename="<memory>"):
    """Recognized current/historical headers; never infer event membership here.

    VERSION/PRODID are required ICS properties. CALSCALE/METHOD/timezone are
    fixed product requirements. CALNAME/CALDESC are descriptive, with the
    explicitly observed historical variants below. Unknown variants block.
    """
    required = {'VERSION', 'PRODID', 'CALSCALE', 'METHOD', 'X-WR-CALNAME', 'X-WR-TIMEZONE'}
    require(required <= set(header), 'ICS_HEADER_REQUIRED')
    require(all(value.strip() for value in header.values()), 'ICS_HEADER_EMPTY')
    require(not (set(header) - required - {'X-WR-CALDESC'}), 'ICS_HEADER_UNKNOWN_PROPERTY')
    for key, value in {'VERSION': '2.0', 'CALSCALE': 'GREGORIAN',
                       'METHOD': 'PUBLISH', 'X-WR-TIMEZONE': 'UTC'}.items():
        require(header[key] == value, 'ICS_HEADER_MISMATCH', key)
    current = {'VERSION': '2.0', 'PRODID': '-//NBA Master Calendar//2026-27 Feed Engine 3.3//ES',
               'CALSCALE': 'GREGORIAN', 'METHOD': 'PUBLISH',
               'X-WR-CALNAME': esc(title), 'X-WR-TIMEZONE': 'UTC'}
    if header == current:
        return
    historical = dict(current, PRODID='-//NBA Master Calendar//2026-27 Premium//ES')
    if title == 'NBA Cup 2026 — Group Play':
        historical['X-WR-CALNAME'] = 'NBA 2026-27 — Emirates NBA Cup Group Play'
        description = 'Calendario NBA 2026-27 generado desde la Base Maestra validada.'
    elif title == 'NBA 2026-27 — Eventos especiales':
        historical['X-WR-CALNAME'] = 'NBA 2026-27 — Partidos Especiales'
        description = 'Calendario NBA 2026-27 generado desde la Base Maestra validada.'
    else:
        team = title.removeprefix('NBA 2026-27 — ')
        require(team in TEAMS, 'ICS_HEADER_UNKNOWN_VARIANT')
        description = f'Calendario 2026-27 de {team} — 80 partidos actualmente definidos.'
    historical['X-WR-CALDESC'] = esc(description)
    require(header == historical, 'ICS_HEADER_UNKNOWN_VARIANT')
    if warnings is not None:
        warnings.append({'code': 'ICS_HISTORICAL_HEADER_WARNING', 'file': filename,
                         'variant': 'premium-2026-27'})


def validate_feed(raw, title, events, records, *, warnings=None,
                  filename="<memory>", strict_folding=False):
    header, actual = parse_calendar(raw, warnings=warnings, filename=filename,
                                    strict_folding=strict_folding)
    validate_header(header, title, warnings, filename)
    expected = {uid_for(e['ID_Partido']): e for e in events}
    seen, semantic = set(), {}
    for item in actual:
        p = item['properties']; uid = p.get('UID')
        require(uid not in seen, 'UID_DUPLICATE', uid or '')
        require(uid in expected, 'UID_UNEXPECTED', uid or '')
        seen.add(uid)
        e = expected[uid]; record = records[e['ID_Partido']]
        utc(p.get('DTSTAMP'))
        start, end = utc(p.get('DTSTART')), utc(p.get('DTEND'))
        require(start == utc(e['Fecha_Hora_UTC'], True) and end == start + timedelta(hours=3), 'SCHEDULE_MISMATCH', uid)
        seq = p.get('SEQUENCE', '')
        require(re.fullmatch(r'0|[1-9][0-9]*', seq) is not None and int(seq) == record['sequence'], 'SEQUENCE_MISMATCH', uid)
        require(p.get('LAST-MODIFIED') == record['last_modified'], 'LAST_MODIFIED_MISMATCH', uid)
        if 'LAST-MODIFIED' in p: utc(p['LAST-MODIFIED'])
        require(p.get('STATUS') == 'CONFIRMED', 'STATUS_UNSUPPORTED', uid)
        alarms = item['alarms']
        require(len(alarms) == 3 and sorted(a.get('TRIGGER', '') for a in alarms) == sorted(['-P1D','-PT2H','-PT30M']) and
                all(a.get('ACTION') == 'DISPLAY' and a.get('DESCRIPTION') for a in alarms), 'ALARMS_MISMATCH', uid)
        # Textual rendering is reused only after independent identity/time/state checks.
        reference = ['BEGIN:VCALENDAR', 'VERSION:2.0'] + event_lines(e, records, p['DTSTAMP']) + ['END:VCALENDAR']
        _, reference_items = parse_calendar(('\r\n'.join(fold_line(line) for line in reference) + '\r\n').encode())
        actual_semantic = normalized(item, e, warnings, filename)
        require(actual_semantic == normalized(reference_items[0], e), 'EVENT_CONTENT_MISMATCH', uid)
        semantic[uid] = actual_semantic
    require(seen == set(expected), 'FEED_EVENT_SET_MISMATCH')
    return semantic


def validate(feeds, master, state, identity, *, warnings=None, strict_folding=False):
    indexed, records = validate_inputs(master, state, identity)
    expected = catalog(list(indexed.values()))
    feeds = Path(feeds)
    require(feeds.is_dir() and not feeds.is_symlink(), 'FEED_ROOT_INVALID')
    paths = {}
    for path in sorted(feeds.rglob('*')):
        require(not path.is_symlink(), 'FEED_SYMLINK', str(path.relative_to(feeds)))
        if path.suffix.lower() == '.ics':
            require(path.is_file(), 'FEED_NOT_FILE')
            paths[path.relative_to(feeds).as_posix()] = path
    require(set(paths) == set(expected), 'FEED_CATALOG_MISMATCH',
            'missing=' + ','.join(sorted(set(expected)-set(paths))) + ';extra=' + ','.join(sorted(set(paths)-set(expected))))
    copies, counts = {}, {}
    for name in sorted(expected):
        title, events = expected[name]
        try:
            semantic = validate_feed(paths[name].read_bytes(), title, events, records,
                                     warnings=warnings, filename=name, strict_folding=strict_folding)
        except Invalid as exc:
            raise Invalid(exc.code, name + (': ' + exc.detail if exc.detail else '')) from exc
        counts[name] = len(semantic)
        for uid, value in semantic.items():
            require(uid not in copies or copies[uid] == value, 'CROSS_FEED_MISMATCH', uid)
            copies[uid] = value
    return counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--feeds', type=Path, default=ROOT/'docs/calendars')
    parser.add_argument('--master', type=Path, default=ROOT/'data/master_snapshot.json')
    parser.add_argument('--state', type=Path, default=ROOT/'data/published_state.json')
    parser.add_argument('--identity-map', type=Path, default=ROOT/'data/nba_game_identity_map.json')
    parser.add_argument('--strict-folding', action='store_true',
                        help='Require physical lines <=75 octets; separate from historical acceptance')
    args = parser.parse_args(argv)
    try:
        inputs = [strict_json(p) for p in (args.master, args.state, args.identity_map)]
    except (OSError, Invalid) as exc:
        print('INPUT_ERROR: ' + (str(exc) if isinstance(exc, Invalid) else 'INPUT_UNREADABLE'))
        return 2
    warnings = []
    def report_warnings():
        for warning in warnings:
            print('WARNING: ' + json.dumps(warning, ensure_ascii=False, sort_keys=True))
    try:
        counts = validate(args.feeds, *inputs, warnings=warnings, strict_folding=args.strict_folding)
    except Invalid as exc:
        report_warnings()
        print('BLOCKED: ' + str(exc))
        return 1
    except OSError:
        report_warnings()
        print('INPUT_ERROR: INPUT_UNREADABLE')
        return 2
    except Exception:
        report_warnings()
        # No traceback or partial success can be mistaken for acceptance.
        print('INPUT_ERROR: VALIDATION_INCOMPLETE')
        return 2
    report_warnings()
    for name, count in sorted(counts.items()):
        print(f'OK {name} | eventos={count}')
    print('PASS: 33 feeds; 1200 partidos; 30 equipos; Cup=60; especiales=32')
    return 0


if __name__ == '__main__':
    sys.exit(main())
