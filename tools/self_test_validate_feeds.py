#!/usr/bin/env python3
"""Deterministic V1.0 acceptance mutations, entirely in external fixtures.

Fixtures are fictional, independently authored ICS; no production builder,
update engine, transaction system or real schedule is run or copied.
"""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
import validate_feeds as v


def check(ok, message):
    if not ok:
        raise AssertionError(message)


def fold(line):
    parts, current = [], ''
    for char in line:
        if len((current + char).encode()) > 75:
            parts.append(current); current = ' '
        current += char
    return '\r\n'.join(parts + [current])


def fixture():
    teams = sorted(v.TEAMS)
    events, records, relations = [], {}, []
    for n in range(1200):
        away, home = teams[(n % 15)*2:(n % 15)*2+2]
        eid = f'NBA2627-{n+1:04d}'
        event = dict(ID_Partido=eid, Temporada='2026-27', Visitante=away, Local=home,
            Fecha_Hora_UTC='2026-10-20T19:00:00Z', Estado='Programado',
            Es_NBA_Cup=n < 60, Es_Partido_Especial=n < 32,
            Arena='Fixture Arena', Ciudad='Fixture City', Estado_Provincia=None,
            País=None, Fase='Temporada Regular', TV_Normalizada=None,
            Streaming_Normalizado=None, Grupo_NBA_Cup='West Group C' if n < 60 else None, Evento_Especial=None,
            Zona_Horaria_Arena='UTC', URL_NBA=None)
        events.append(event)
        records[eid] = dict(uid=eid+'@nba-master-calendar.local', sequence=0,
            fingerprint=v.fingerprint(event), status='ACTIVE', last_modified=None)
        relations.append(dict(ID_Partido=eid, gameId=f'00226{n+1:05d}',
            Visitante_Tricode=v.TEAMS[away], Local_Tricode=v.TEAMS[home],
            Fecha_Hora_UTC_Validacion='2026-10-19T19:00:00Z'))
    files = {
        'master.json': json.dumps(dict(season='2026-27', events=events)).encode(),
        'state.json': json.dumps(dict(schema_version='3.3.0', season='2026-27', events=records)).encode(),
        'identity.json': json.dumps(dict(schema_version='1.0.0', season='2026-27', events=relations)).encode(),
    }
    # Select independently of catalog(), so omissions/membership bugs are detectable.
    selections = [('nba-2026-27-completo.ics', 'NBA 2026-27 — Completo', events),
        ('nba-2026-27-cup-group-play.ics', 'NBA Cup 2026 — Group Play', events[:60]),
        ('nba-2026-27-eventos-especiales.ics', 'NBA 2026-27 — Eventos especiales', events[:32])]
    for team in teams:
        selections.append(('teams/'+team.lower().replace(' ', '-')+'.ics',
            'NBA 2026-27 — '+team, [e for e in events if team in (e['Visitante'],e['Local'])]))
    for name, title, selected in selections:
        lines = ['BEGIN:VCALENDAR','VERSION:2.0',
            'PRODID:-//NBA Master Calendar//2026-27 Feed Engine 3.3//ES',
            'CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:'+title,'X-WR-TIMEZONE:UTC']
        for e in selected:
            base = e['Visitante']+' @ '+e['Local']
            summary = ('[NBA CUP] ' if e['Es_NBA_Cup'] else '') + base
            description = ('NBA 2026-27 — Temporada Regular\\n'
                'Hora Santiago: 20-10-2026 16:00\\n'
                'Hora Punta Arenas/Magallanes: 20-10-2026 16:00\\n'
                'TV nacional EE.UU.: No indicado\\nStreaming: No indicado\\n'+
                ('Grupo NBA Cup: West Group C\\n' if e['Es_NBA_Cup'] else '')+
                'ID maestro: '+e['ID_Partido']+'\\nFuente base: NBA.com\\n'
                'Duración del calendario: 3 h estimadas\\; el término real del partido puede variar.')
            lines += ['BEGIN:VEVENT','UID:'+records[e['ID_Partido']]['uid'],
                'DTSTAMP:20261001T000000Z','DTSTART:20261020T190000Z',
                'DTEND:20261020T220000Z','SUMMARY:'+summary,
                'LOCATION:Fixture Arena\\, Fixture City','DESCRIPTION:'+description,
                'STATUS:CONFIRMED','TRANSP:TRANSPARENT','CATEGORIES:NBA 2026-27','SEQUENCE:0']
            for trigger, label in [('-P1D','partido mañana'),('-PT2H','partido en 2 horas'),('-PT30M','partido en 30 minutos')]:
                lines += ['BEGIN:VALARM','ACTION:DISPLAY','DESCRIPTION:NBA: '+label+' — '+base,
                          'TRIGGER:'+trigger,'END:VALARM']
            lines += ['END:VEVENT']
        lines += ['END:VCALENDAR']
        files['calendars/'+name] = ('\r\n'.join(fold(line) for line in lines)+'\r\n').encode()
    return files


def main():
    files = fixture()
    passed = []
    with tempfile.TemporaryDirectory(prefix='plannersport-feed-validation-') as tmp:
        root = Path(tmp)
        def restore():
            for p in root.rglob('*'):
                if p.is_file() or p.is_symlink(): p.unlink()
            for name, raw in files.items():
                p=root/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)
        def digest():
            return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in root.rglob('*') if p.is_file()}
        argv=['--feeds',str(root/'calendars'),'--master',str(root/'master.json'),
              '--state',str(root/'state.json'),'--identity-map',str(root/'identity.json')]
        def run():
            out=io.StringIO()
            with contextlib.redirect_stdout(out): result=v.main(argv)
            return result,out.getvalue()
        def case(name, mutate=None, code=None, exit_code=1):
            restore()
            if mutate: mutate()
            before=digest()
            result,output=run()
            check(result == exit_code, name+': '+output)
            if code: check(code in output, name+': diagnostic '+output)
            check(('PASS:' in output) == (exit_code == 0), name+': misleading PASS')
            check(digest()==before, name+': inputs changed')
            passed.append(name)
        full='calendars/nba-2026-27-completo.ics'
        team='calendars/teams/atlanta-hawks.ics'
        def replace(name, old, new):
            p=root/name; raw=p.read_bytes(); check(old in raw,'fixture mutation absent')
            p.write_bytes(raw.replace(old,new,1))
        def data(name, mutate):
            p=root/name; obj=json.loads(p.read_bytes()); mutate(obj); p.write_text(json.dumps(obj))
        def first_event(name):
            raw=(root/name).read_bytes(); start=raw.index(b'BEGIN:VEVENT\r\n')
            end=raw.index(b'END:VEVENT\r\n',start)+len(b'END:VEVENT\r\n')
            return raw[start:end]
        case('baseline, zero sequence without last-modified',exit_code=0)
        case('missing catalog',lambda:(root/team).unlink(),'FEED_CATALOG_MISMATCH')
        case('additional feed',lambda:(root/'calendars/extra.ics').write_bytes(b'x'),'FEED_CATALOG_MISMATCH')
        case('duplicate UID',lambda:replace(full,b'END:VCALENDAR',first_event(full)+b'END:VCALENDAR'),'UID_DUPLICATE')
        case('unknown UID',lambda:replace(full,b'NBA2627-0001@',b'NBA2627-9999@'),'UID_UNEXPECTED')
        case('wrong team membership',lambda:replace(team,b'NBA2627-0001@',b'NBA2627-0002@'),'UID_UNEXPECTED')
        case('wrong schedule',lambda:replace(full,b'DTSTART:20261020T190000Z',b'DTSTART:20261020T200000Z'),'SCHEDULE_MISMATCH')
        case('wrong duration',lambda:replace(full,b'DTEND:20261020T220000Z',b'DTEND:20261020T230000Z'),'SCHEDULE_MISMATCH')
        case('wrong sequence',lambda:replace(full,b'SEQUENCE:0',b'SEQUENCE:1'),'SEQUENCE_MISMATCH')
        case('negative sequence',lambda:replace(full,b'SEQUENCE:0',b'SEQUENCE:-1'),'SEQUENCE_MISMATCH')
        case('wrong fingerprint',lambda:data('state.json',lambda x:x['events']['NBA2627-0001'].update(fingerprint='0'*64)),'STATE_FINGERPRINT_MISMATCH')
        case('state identity divergence',lambda:data('state.json',lambda x:x['events'].pop('NBA2627-0001')),'STATE_IDS_MISMATCH')
        case('wrong Cup membership',lambda:replace('calendars/nba-2026-27-cup-group-play.ics',b'NBA2627-0001@',b'NBA2627-0061@'),'UID_UNEXPECTED')
        case('wrong special membership',lambda:replace('calendars/nba-2026-27-eventos-especiales.ics',b'NBA2627-0001@',b'NBA2627-0033@'),'UID_UNEXPECTED')
        case('truncated ICS',lambda:replace(full,b'END:VCALENDAR\r\n',b''),'ICS_ENVELOPE')
        case('invalid UTF8',lambda:replace(full,b'CONFIRMED',b'\xffONFIRMED'),'ICS_UTF8')
        case('duplicate property',lambda:replace(full,b'SEQUENCE:0',b'SEQUENCE:0\r\nSEQUENCE:0'),'ICS_PROPERTY_DUPLICATE')
        case('impossible date',lambda:replace(full,b'DTSTART:20261020T190000Z',b'DTSTART:20260230T190000Z'),'UTC_INVALID')
        case('cancelled ICS',lambda:replace(full,b'STATUS:CONFIRMED',b'STATUS:CANCELLED'),'STATUS_UNSUPPORTED')
        case('cancelled state',lambda:data('state.json',lambda x:x['events']['NBA2627-0001'].update(status='CANCELLED')),'STATUS_UNSUPPORTED')
        case('historical DTSTAMP accepted',lambda:replace(team,b'DTSTAMP:20261001T000000Z',b'DTSTAMP:20260901T000000Z'),exit_code=0)
        case('last-modified inconsistent',lambda:replace(full,b'SEQUENCE:0',b'SEQUENCE:0\r\nLAST-MODIFIED:20261001T000000Z'),'LAST_MODIFIED_MISMATCH')
        case('alarm missing',lambda:replace(full,b'TRIGGER:-P1D',b'TRIGGER:-P2D'),'ALARMS_MISMATCH')
        case('semantic copy mismatch',lambda:replace(team,b'Fixture Arena',b'Wrongxx Arena'),'EVENT_CONTENT_MISMATCH')
        case('LF rejected',lambda:(root/full).write_bytes((root/full).read_bytes().replace(b'\r\n',b'\n')),'ICS_CRLF')
        case('nesting invalid',lambda:replace(full,b'BEGIN:VALARM',b'BEGIN:VEVENT'),'ICS_NESTING')
        case('duplicate master ID',lambda:data('master.json',lambda x:x['events'][1].update(ID_Partido='NBA2627-0001')),'MASTER_ID_DUPLICATE')
        case('unknown team',lambda:data('master.json',lambda x:x['events'][0].update(Local='Unknown')),'TEAM_INVALID')
        case('identity tricode mismatch',lambda:data('identity.json',lambda x:x['events'][0].update(Local_Tricode='WAS')),'IDENTITY_TEAM_MISMATCH')
        case('identity duplicate game',lambda:data('identity.json',lambda x:x['events'][1].update(gameId='0022600001')),'IDENTITY_GAME_INVALID')
        case('Cup coverage changed',lambda:data('master.json',lambda x:x['events'][0].update(Es_NBA_Cup=False)),'CUP_COVERAGE')
        case('special coverage changed',lambda:data('master.json',lambda x:x['events'][0].update(Es_Partido_Especial=False)),'SPECIAL_COVERAGE')
        case('missing state UID',lambda:data('state.json',lambda x:x['events']['NBA2627-0001'].pop('uid')),'STATE_UID_MISMATCH')
        case('boolean state sequence',lambda:data('state.json',lambda x:x['events']['NBA2627-0001'].update(sequence=True)),'STATE_SEQUENCE_INVALID')
        case('master impossible date',lambda:data('master.json',lambda x:x['events'][0].update(Fecha_Hora_UTC='2026-02-30T19:00:00Z')),'UTC_INVALID')
        case('floating time',lambda:replace(full,b'DTSTART:20261020T190000Z',b'DTSTART:20261020T190000'),'UTC_INVALID')
        case('unsupported parameter',lambda:replace(full,b'DTSTART:',b'DTSTART;TZID=UTC:'),'ICS_PROPERTY_UNSUPPORTED')
        case('long line retains semantic rejection',lambda:replace(full,b'LOCATION:Fixture Arena\\, Fixture City',b'LOCATION:'+b'x'*76),'EVENT_CONTENT_MISMATCH')
        def description_change(name, transform, eid='NBA2627-0001'):
            p = root/name
            logical = []
            for line in p.read_bytes().decode().split('\r\n')[:-1]:
                if line.startswith((' ', '\t')): logical[-1] += line[1:]
                else: logical.append(line)
            in_event = False
            target = False
            in_alarm = False
            for index, line in enumerate(logical):
                if line == 'BEGIN:VEVENT': in_event = True; target = False
                elif line == 'END:VEVENT': in_event = False
                elif line == 'BEGIN:VALARM': in_alarm = True
                elif line == 'END:VALARM': in_alarm = False
                elif in_event and line.startswith('UID:'): target = line == 'UID:'+eid+'@nba-master-calendar.local'
                elif target and not in_alarm and line.startswith('DESCRIPTION:'):
                    logical[index] = 'DESCRIPTION:'+transform(line[len('DESCRIPTION:'):])
            p.write_bytes(('\r\n'.join(fold(line) for line in logical)+'\r\n').encode())
        current_label = 'Grupo NBA Cup: West Group C'
        old_label = 'Emirates NBA Cup — West Group C'
        def old_description(name=team):
            description_change(name, lambda d:d.replace(current_label,old_label,1))
        case('current Cup declaration accepted',exit_code=0)
        case('historical and current Cup copies accepted',old_description,
             'ICS_HISTORICAL_CUP_DESCRIPTION_WARNING',0)
        case('historical Cup feed accepted',lambda:old_description('calendars/nba-2026-27-cup-group-play.ics'),
             'ICS_HISTORICAL_CUP_DESCRIPTION_WARNING',0)
        case('wrong Cup group',lambda:description_change(team,lambda d:d.replace(current_label,'Grupo NBA Cup: East Group A',1)),
             'CUP_GROUP_MISMATCH')
        case('missing Cup group',lambda:description_change(team,lambda d:d.replace(current_label+'\\n','',1)),
             'CUP_DECLARATION_COUNT')
        case('duplicate Cup group',lambda:description_change(team,lambda d:d.replace(current_label,current_label+'\\n'+current_label,1)),
             'CUP_DECLARATION_COUNT')
        case('contradictory Cup group',lambda:description_change(team,lambda d:d.replace(current_label,current_label+'\\nEmirates NBA Cup — East Group A',1)),
             'CUP_DECLARATION_COUNT')
        case('Cup declaration on non-Cup event',lambda:description_change(team,lambda d:d+'\\n'+old_label,'NBA2627-0061'),
             'CUP_DECLARATION_UNEXPECTED')
        case('unknown Cup label spelling',lambda:description_change(team,lambda d:d.replace(current_label,'Grupo NBA Cup - West Group C',1)),
             'CUP_GROUP_MISMATCH')
        def historical_mutation(old, new):
            old_description()
            replace(team,old,new)
        case('historical Cup other description text rejected',lambda:description_change(team,
             lambda d:d.replace(current_label,old_label,1).replace('Fuente base: NBA.com','Fuente base: Other',1)),
             'EVENT_CONTENT_MISMATCH')
        case('historical Cup schedule mutation rejected',lambda:historical_mutation(b'DTSTART:20261020T190000Z',b'DTSTART:20261020T200000Z'),
             'SCHEDULE_MISMATCH')
        case('historical Cup location mutation rejected',lambda:historical_mutation(b'LOCATION:Fixture Arena',b'LOCATION:Wrongxx Arena'),
             'EVENT_CONTENT_MISMATCH')
        case('historical Cup status mutation rejected',lambda:historical_mutation(b'STATUS:CONFIRMED',b'STATUS:CANCELLED'),
             'STATUS_UNSUPPORTED')
        case('historical Cup sequence mutation rejected',lambda:historical_mutation(b'SEQUENCE:0',b'SEQUENCE:1'),
             'SEQUENCE_MISMATCH')
        case('historical Cup alarm mutation rejected',lambda:historical_mutation(b'TRIGGER:-P1D',b'TRIGGER:-P2D'),
             'ALARMS_MISMATCH')
        case('missing Cup master group',lambda:data('master.json',lambda x:x['events'][0].update(Grupo_NBA_Cup=None)),
             'STATE_FINGERPRINT_MISMATCH')
        restore(); old_description(); initial=digest(); first=run(); second=run()
        check(first == second and first[0] == 0 and digest() == initial,'Cup diagnostics not deterministic/read-only')
        cup_warnings=[json.loads(line[len('WARNING: '):]) for line in first[1].splitlines()
                      if 'ICS_HISTORICAL_CUP_DESCRIPTION_WARNING' in line]
        check(cup_warnings == [dict(code='ICS_HISTORICAL_CUP_DESCRIPTION_WARNING',
              file='teams/atlanta-hawks.ics',uid='NBA2627-0001@nba-master-calendar.local',group='West Group C')],
              'Cup warning attribution')
        passed.append('Cup warning deterministic and fixtures intact')
        # Recognized historical metadata is independent of event expectations.
        def historical(name, old_title=None, new_title=None):
            replace(name,b'Feed Engine 3.3',b'Premium')
            if old_title is not None:
                replace(name,old_title.encode(),new_title.encode())
            description = ('Calendario 2026-27 de Atlanta Hawks — 80 partidos actualmente definidos.'
                if name == team else 'Calendario NBA 2026-27 generado desde la Base Maestra validada.')
            replace(name,b'X-WR-TIMEZONE:UTC',('X-WR-CALDESC:'+description+'\r\nX-WR-TIMEZONE:UTC').encode())
        case('historical team header accepted',lambda:historical(team),'ICS_HISTORICAL_HEADER_WARNING',0)
        case('historical Cup header accepted',lambda:historical('calendars/nba-2026-27-cup-group-play.ics',
             'NBA Cup 2026 — Group Play','NBA 2026-27 — Emirates NBA Cup Group Play'),'ICS_HISTORICAL_HEADER_WARNING',0)
        case('historical specials header accepted',lambda:historical('calendars/nba-2026-27-eventos-especiales.ics',
             'NBA 2026-27 — Eventos especiales','NBA 2026-27 — Partidos Especiales'),'ICS_HISTORICAL_HEADER_WARNING',0)
        case('unknown header variant',lambda:replace(full,b'Feed Engine 3.3',b'Unknown Engine'),'ICS_HEADER_UNKNOWN_VARIANT')
        case('unknown descriptive title',lambda:replace(team,b'X-WR-CALNAME:NBA 2026-27',b'X-WR-CALNAME:Unknown 2026'),'ICS_HEADER_UNKNOWN_VARIANT')
        case('unknown header property',lambda:replace(full,b'VERSION:2.0',b'VERSION:2.0\r\nX-UNKNOWN:value'),'ICS_HEADER_UNKNOWN_PROPERTY')
        case('duplicate header',lambda:replace(full,b'VERSION:2.0',b'VERSION:2.0\r\nVERSION:2.0'),'ICS_PROPERTY_DUPLICATE')
        case('empty header',lambda:replace(full,b'METHOD:PUBLISH',b'METHOD:'),'ICS_HEADER_EMPTY')
        case('missing header',lambda:replace(full,b'METHOD:PUBLISH\r\n',b''),'ICS_HEADER_REQUIRED')
        case('orphan continuation',lambda:(root/full).write_bytes(b' orphan\r\n'+(root/full).read_bytes()),'ICS_CONTINUATION')
        case('empty physical line',lambda:replace(full,b'VERSION:2.0',b'VERSION:2.0\r\n'),'ICS_EMPTY_LINE')
        case('tab continuation accepted',lambda:replace(full,b'LOCATION:Fixture Arena\\, Fixture City',b'LOCATION:Fixture\r\n\t Arena\\, Fixture City'),exit_code=0)
        case('single space word folding accepted',lambda:replace(full,b'LOCATION:Fixture Arena\\, Fixture City',b'LOCATION:Fix\r\n ture Arena\\, Fixture City'),exit_code=0)
        def historical_semantic_error():
            historical(team)
            replace(team,b'DTSTART:20261020T190000Z',b'DTSTART:20261020T200000Z')
        case('historical header preserves schedule rejection',historical_semantic_error,'SCHEDULE_MISMATCH')
        # Boundary cases directly assert the parser's byte counts and unfolding.
        for size in (75,76,77,96):
            for multibyte in (False,True):
                suffix = 'é' if multibyte else ''
                logical = 'DESCRIPTION:'+'a'*(size-len('DESCRIPTION:')-len(suffix.encode()))+suffix
                raw = ('BEGIN:VCALENDAR\r\nVERSION:2.0\r\n'+logical+'\r\nEND:VCALENDAR\r\n').encode()
                warnings=[]
                header,items=v.parse_calendar(raw,warnings=warnings,filename='boundary.ics')
                check(header['DESCRIPTION']==logical.split(':',1)[1] and not items,'boundary content altered')
                expected=[] if size==75 else [dict(code='ICS_LINE_LENGTH_WARNING',file='boundary.ics',
                    line=3,octets=size,property='DESCRIPTION')]
                check(warnings==expected,'warning metadata differs')
                try:
                    v.parse_calendar(raw,strict_folding=True)
                except v.Invalid as exc:
                    check(size>75 and exc.code=='ICS_FOLDING','strict boundary rejection')
                else:
                    check(size==75,'strict boundary accepted long line')
                passed.append(f'boundary {size} octets '+('UTF8' if multibyte else 'ASCII'))
        raw=b'BEGIN:VCALENDAR\r\nDESCRIPTION:abc\r\n def'+b'x'*73+b'\r\nEND:VCALENDAR\r\n'
        warnings=[]
        header,_=v.parse_calendar(raw,warnings=warnings,filename='continuation.ics')
        check(header['DESCRIPTION']=='abcdef'+'x'*73,'long continuation reconstruction')
        check(warnings==[dict(code='ICS_LINE_LENGTH_WARNING',file='continuation.ics',line=3,
              octets=77,property='DESCRIPTION')],'continuation warning attribution')
        passed.append('long continuation attributes owning property')
        case('header mismatch',lambda:replace(full,b'METHOD:PUBLISH',b'METHOD:CANCEL'),'ICS_HEADER_MISMATCH')
        case('property order accepted',lambda:replace(full,b'STATUS:CONFIRMED\r\nTRANSP:TRANSPARENT',b'TRANSP:TRANSPARENT\r\nSTATUS:CONFIRMED'),exit_code=0)
        case('equivalent folding accepted',lambda:replace(full,b'LOCATION:Fixture Arena\\, Fixture City',b'LOCATION:Fixture\r\n  Arena\\, Fixture City'),exit_code=0)
        def positive_sequence():
            data('state.json',lambda x:x['events']['NBA2627-0001'].update(sequence=1,last_modified='20261001T000000Z'))
            for name in files:
                if name.endswith('.ics') and b'UID:NBA2627-0001@' in (root/name).read_bytes():
                    replace(name,b'SEQUENCE:0',b'SEQUENCE:1\r\nLAST-MODIFIED:20261001T000000Z')
        case('positive sequence with last-modified accepted',positive_sequence,exit_code=0)
        case('master jointly incomplete',lambda:data('master.json',lambda x:x['events'].pop()),'MASTER_COVERAGE')
        case('unreadable input',lambda:(root/'state.json').unlink(),'INPUT_UNREADABLE',2)
        case('malformed JSON',lambda:(root/'state.json').write_bytes(b'{'),'JSON_INVALID',2)
        case('duplicate JSON key',lambda:replace('state.json',b'"season": "2026-27"',b'"season":"2026-27","season":"2026-27"'),'JSON_DUPLICATE_KEY',2)
        restore(); before=digest(); a=run(); b=run()
        check(a==b and a[0]==0 and digest()==before,'deterministic read-only result')
        passed.append('deterministic result and unchanged inputs')
        # Exercise CLI in an independent process; -B prevents cache files.
        command=[sys.executable,'-B',str(Path(v.__file__).resolve()),*argv]
        cli=subprocess.run(command,capture_output=True,text=True,check=False)
        check(cli.returncode==0 and cli.stdout==a[1] and not cli.stderr,'CLI mismatch')
        check(digest()==before,'CLI modified fixture')
        passed.append('independent CLI read-only acceptance')
    print(json.dumps({'suite':'validate-feeds-v1','passed':len(passed),'cases':passed},ensure_ascii=False,sort_keys=True))


if __name__ == '__main__':
    main()
