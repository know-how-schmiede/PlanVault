"""Fiktiver vollständiger Kalenderimport und transaktionale Archivfreigabe."""
from collections import Counter
from dataclasses import replace
from datetime import date, time, timedelta
import json
import os
import sqlite3

import pytest

from backend import create_app
from backend.importer.calendar import build_candidate, validate_review, run_calendar_import
from backend.importer.calendar_policy import parse_policy, digest, series_digest
from backend.importer.details import DetailImportError, DetailSample, DetailResult
from backend.importer.http import SourceClient, SourceDocument
from backend.importer.coverage import WeekResult
from backend.importer.occurrences import ObservedOccurrence, read_week_occurrences
from backend.parser.course import CourseDetail, ScheduleSeries
from backend.parser.normalize import normalize_course, CourseContext
from backend.storage.archive import (begin_run, stage_run, fail_run, publish_run, read_snapshot,
    get_candidate, history, import_lock, backup_archive)
from tests.test_weekly_presence import references
from tests.test_view_comparison import POLICY


def policy_data():
    return dict(schema=1, semester='DEMO-Semester', study_key='DEMO', regulations_key='PO',
                study_title='Fiktives Studium', start='2026-12-28', end='2027-01-10', breaks=[])


def audit():
    return dict(status='needs_review', all_requested_weeks_observed=True, unavailable_weeks=[],
                failed_weeks=[], comparison={'reference_sets_equal': True}, unresolved_day_notices=[])


def course_detail(*, recurrence='Einzel', day=date(2026,12,28), note=None, execution=None, cancellation=None):
    series = ScheduleSeries(day.weekday(), time(8), time(9), day, day, recurrence,
                            'DEMO-RAUM', 'Fiktive Lehrperson', execution, note, cancellation)
    course = CourseDetail(None, '<script>FIKTIV</script>', None, 'Demo', 'DEMO-Semester', (series,), ())
    try:
        preview = normalize_course(course, CourseContext('A', 'DEMO', 'PO', 'DEMO-Semester', True))
    except ValueError:
        preview = None
    return DetailResult('A', 1, 'preview' if preview else 'normalization_requires_review', preview,
                         course if not preview else None, 'unsupported_series_note' if not preview else None, course)


def observation(day='2026-12-28', **kwargs):
    values = dict(reference_key='A', local_date=day, start_time='08:00:00', end_time='09:00:00',
                  room='DEMO-RAUM', event_type='Demo', supplementary_text='FIKTIVE GRUPPE')
    values.update(kwargs)
    return ObservedOccurrence(**values)


def candidate(detail=None, observed=None, rules=None, report=None):
    d = detail or course_detail()
    return build_candidate(parse_policy(rules or policy_data()), references((d,)),
                           DetailSample(1,1,(d,)), tuple([observation()] if observed is None else observed),
                           report or audit())


def approval(c):
    return dict(schema=1, candidate_digest=c['digest'],
                decisions={r['id']: {'decision':'confirmed','evidence':'Fiktiver Prüfbeleg'} for r in c['reviews']})


def test_exact_occurrence_comparison_and_bound_review():
    c = candidate()
    assert not c['hard_blockers'] and len(c['events']) == 1 and not c['complete']
    assert {'weekend_inventory', 'groups_and_instructors', 'semester_and_study_context',
            'academic_break_policy'} == {r['code'] for r in c['reviews']}
    validate_review(c, approval(c))
    c['events'][0]['room'] = 'Manipuliert'
    with pytest.raises(DetailImportError): validate_review(c, approval(c))


@pytest.mark.parametrize('field,value', [('room','OTHER'),('start_time','08:15:00'),
                                         ('end_time','09:15:00'),('local_date','2026-12-29'),
                                         ('event_type','Anders')])
def test_wrong_fields_are_hard_blockers(field,value):
    c = candidate(observed=[observation(**{field:value})])
    assert 'occurrence_fields_mismatch' in {b['code'] for b in c['hard_blockers']}
    with pytest.raises(DetailImportError): validate_review(c, approval(c))


def test_duplicate_source_block_cannot_be_hidden_by_set_comparison():
    c = candidate(observed=[observation(),observation()])
    assert c['hard_blockers'] == [{'code':'unexpected_source_occurrence','detail_number':1,
                                   'local_date':'2026-12-28','count':1}]


def test_explicit_break_only_suppresses_absent_weekly_series():
    rules = policy_data(); rules['breaks'] = [dict(start='2026-12-28',end='2026-12-28',evidence='Fiktiver Ferienbeleg')]
    c = candidate(course_detail(recurrence='woch'), [], rules)
    assert c['suppressed'][0]['local_date'] == '2026-12-28'
    # Kein leerer Stand darf durch die Ferienregel freigegeben werden.
    assert c['hard_blockers'] == [{'code':'empty_calendar'}]
    visible = candidate(course_detail(recurrence='woch'), [observation()], rules)
    assert len(visible['events']) == 1 and not visible['suppressed'] and not visible['hard_blockers']
    single = candidate(course_detail(), [], rules)
    assert 'occurrence_fields_mismatch' in {r['code'] for r in single['hard_blockers']}


def test_unnamed_day_is_resolved_only_inside_explicit_break():
    report = audit();report['unresolved_day_notices']=[{'local_date':'2026-12-28','kind':'unnamed'}]
    assert any(r['code']=='source_day_notice' for r in candidate(report=report)['reviews'])
    rules = policy_data();rules['breaks']=[dict(start='2026-12-28',end='2026-12-28',evidence='Fiktiver Beleg')]
    assert not any(r['code']=='source_day_notice' for r in candidate(rules=rules,report=report)['reviews'])
    report['unresolved_day_notices'][0]['kind']='unclassified'
    assert any(r['code']=='source_day_notice' for r in candidate(rules=rules,report=report)['reviews'])


def test_exact_annotation_rule_retains_original_and_requires_review():
    d = course_detail(note='Fiktiver Begrüßungshinweis')
    assert candidate(d)['hard_blockers'][0]['code']=='unsupported_series_note'
    rules=policy_data();rules['annotation_rules']=[dict(series_digest=series_digest(d.source_course.series[0]),field='note',effect='annotation')]
    c=candidate(d,rules=rules)
    assert not c['hard_blockers'] and any(r['code']=='course_notes' for r in c['reviews'])
    assert c['inventory'][0]['series'][0]['note']=='Fiktiver Begrüßungshinweis'
    changed=course_detail(note='Fiktiver Begrüßungshinweis geändert')
    assert 'unused_annotation_rules' in {b['code'] for b in candidate(changed,rules=rules)['hard_blockers']}


def test_weekend_remains_in_calendar_but_needs_independent_review():
    c=candidate(course_detail(day=date(2027,1,2)),[])
    assert not c['hard_blockers'] and len(c['events'])==1
    assert any(r['code']=='weekend_inventory' for r in c['reviews'])


def test_cancellation_is_not_recreated_and_visible_cancelled_slot_blocks():
    c=candidate(course_detail(cancellation='28.12.2026'),[])
    assert c['hard_blockers']==[{'code':'empty_calendar'}]
    assert any(b['code']=='unexpected_source_occurrence' for b in candidate(course_detail(cancellation='28.12.2026'))['hard_blockers'])


@pytest.mark.parametrize('change', [lambda p:p.update(schema=True), lambda p:p.update(start='bad'),
    lambda p:p.update(end='2029-01-01'),lambda p:p.update(study_key='https://example.invalid'),
    lambda p:p.update(breaks=[dict(start='2027-01-20',end='2027-01-21',evidence='Fiktiv')]),
    lambda p:p.update(annotation_rules=[dict(series_digest='bad',field='note',effect='annotation')]),
    lambda p:p.update(extra='unknown')])
def test_invalid_policy_is_rejected(change):
    p=policy_data();change(p)
    with pytest.raises(DetailImportError):parse_policy(p)


@pytest.mark.parametrize('mutate', [lambda a:a.update(candidate_digest='0'*64),lambda a:a.update(schema=True),
    lambda a:a.update(decisions={}),lambda a:a['decisions'].update(extra={'decision':'confirmed','evidence':'Fiktiv'}),
    lambda a:next(iter(a['decisions'].values())).update(decision='pending'),
    lambda a:next(iter(a['decisions'].values())).update(evidence='')])
def test_unbound_or_partial_approval_is_rejected(mutate):
    c=candidate();a=approval(c);mutate(a)
    with pytest.raises(DetailImportError):validate_review(c,a)


def grid_html(*, rowspan=1, room='DEMO-RAUM', day_index=0):
    names=('Montag','Dienstag','Mittwoch','Donnerstag','Freitag')
    headers=''.join(f'<th>{n} {date(2026,12,28)+timedelta(days=i):%d.%m.%Y}</th>' for i,n in enumerate(names))
    rows=['<a href="/detail?record=1">Fiktiver Kurs</a>', '08:00 - 09:00 (Einzel)',
          'Start: 28.12.2026','Ende: 28.12.2026',f'Raum: {room}','Demo','FIKTIVE GRUPPE','']
    block='<table>'+''.join(f'<tr><td class="{"plan5a" if i==0 else "notiz"}">{value}</td></tr>' for i,value in enumerate(rows))+'</table>'
    cells=''.join(f'<td rowspan="{rowspan}">{block if i==day_index else ""}</td>' for i in range(5))
    return f'<table><tr><th colspan="2">Zeit</th>{headers}</tr><tr><td>8</td><td></td>{cells}</tr></table>'


def test_parser_assigns_column_and_reads_exact_fields():
    with SourceClient('https://example.invalid/start') as client:
        observed=read_week_occurrences(client,SourceDocument(grid_html(), 'https://example.invalid/view'),
                                       WeekResult(2026,53,'ok'),identity_policy=POLICY)
    assert len(observed)==1 and observed[0].local_date=='2026-12-28'
    assert observed[0].room=='DEMO-RAUM' and observed[0].start_time=='08:00:00'


@pytest.mark.parametrize('html', [grid_html(day_index=1), grid_html().replace('08:00 -','not-a-time -'),
                                grid_html().replace('colspan="2"','colspan="99"'),
                                grid_html().replace('Ende:','Unbekannt:')])
def test_parser_rejects_ambiguous_or_inconsistent_fields(html):
    with SourceClient('https://example.invalid/start') as client,pytest.raises(DetailImportError):
        read_week_occurrences(client,SourceDocument(html,'https://example.invalid/view'),WeekResult(2026,53,'ok'),identity_policy=POLICY)


@pytest.fixture
def database(tmp_path):return str(tmp_path/'archive.sqlite')


def staged(database,c=None):
    c=c or candidate(); run=begin_run(database,c['policy']);stage_run(database,run,c);return run,c


def test_archive_publication_failure_and_deduplication(database):
    run,c=staged(database)
    assert read_snapshot(database) is None
    first=publish_run(database,run,approval(c));assert first['status']=='published'
    valid=read_snapshot(database);assert valid['complete'] and valid['snapshot_id']==first['snapshot_id']
    failed=begin_run(database,c['policy']);fail_run(database,failed)
    assert read_snapshot(database)['snapshot_id']==first['snapshot_id']
    assert read_snapshot(database)['last_attempt_status']=='failed'
    bad=candidate(observed=[]);run_bad,_=staged(database,bad)
    with pytest.raises(DetailImportError):publish_run(database,run_bad,approval(bad))
    assert read_snapshot(database)['snapshot_id']==first['snapshot_id']
    run2,c2=staged(database);second=publish_run(database,run2,approval(c2))
    assert second['status']=='unchanged' and second['snapshot_id']==first['snapshot_id']
    assert len(history(database))==4
    with pytest.raises(DetailImportError):publish_run(database,run2,approval(c2))
    assert os.stat(database).st_mode & 0o777 == 0o600


def test_wrong_run_scope_and_tampered_candidate_never_stage(database):
    c=candidate();p=dict(c['policy'],semester='OTHER');run=begin_run(database,p)
    with pytest.raises(DetailImportError):stage_run(database,run,c)
    c['events'][0]['title']='Manipuliert'
    with pytest.raises(DetailImportError):stage_run(database,run,c)


def test_import_lock_excludes_parallel_runs(database):
    with import_lock(database):
        with pytest.raises(DetailImportError):
            with import_lock(database):pytest.fail('Zweite Sperre unerwartet möglich')
    with import_lock(database):pass


def test_backup_and_restore_preserve_published_and_failed_runs(database,tmp_path):
    run,c=staged(database);publish_run(database,run,approval(c))
    failed=begin_run(database,c['policy']);fail_run(database,failed)
    backup=str(tmp_path/'backup.sqlite');backup_archive(database,backup)
    restored=str(tmp_path/'restored.sqlite');backup_archive(backup,restored)
    assert read_snapshot(database)==read_snapshot(restored)
    assert history(database)==history(restored)
    with pytest.raises(DetailImportError):backup_archive(database,backup)


def test_unknown_database_schema_is_never_modified(database):
    with sqlite3.connect(database) as db:db.execute('CREATE TABLE unrelated(x)')
    with pytest.raises(DetailImportError):begin_run(database,policy_data())
    with sqlite3.connect(database) as db:
        assert [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]==['unrelated']


def test_corrupt_snapshot_is_rejected(database):
    run,c=staged(database);publish_run(database,run,approval(c))
    with sqlite3.connect(database) as db:db.execute("UPDATE snapshots SET payload='{}'")
    with pytest.raises(DetailImportError):read_snapshot(database)


def test_archive_web_is_local_escaped_and_keeps_snapshot_navigation(database,monkeypatch):
    run,c=staged(database);published=publish_run(database,run,approval(c))
    app=create_app({'TESTING':True,'ARCHIVE_DATABASE':database})
    monkeypatch.setattr(SourceClient,'fetch',lambda *a,**k:pytest.fail('Webseite darf nicht importieren'))
    client=app.test_client();response=client.get('/archiv')
    assert response.status_code==200 and response.headers['Cache-Control']=='no-store'
    html=response.get_data(as_text=True)
    assert 'Freigegebener Archivstand' in html and 'V0.0.30' in html
    assert '&lt;script&gt;FIKTIV&lt;/script&gt;' in html and '<script>FIKTIV</script>' not in html
    assert f'snapshot={published["snapshot_id"]}' in html and '2027-W01' in html
    assert client.get('/archiv?week=2027-W01').status_code==200
    assert client.get('/archiv?snapshot=../../secret').status_code==400
    assert client.get('/archiv?snapshot='+str(2**80)).status_code==400
    assert client.get('/archiv?snapshot='+'9'*5000).status_code==400


def test_web_does_not_create_database(tmp_path):
    target=tmp_path/'missing.sqlite'
    client=create_app({'TESTING':True,'ARCHIVE_DATABASE':str(target)}).test_client()
    assert client.get('/archiv').status_code==200 and not target.exists()


def test_review_export_is_private_and_cannot_overwrite(database,tmp_path):
    run,c=staged(database);app=create_app({'TESTING':True,'ARCHIVE_DATABASE':database});runner=app.test_cli_runner()
    target=tmp_path/'packet.review.json'
    result=runner.invoke(args=['archive-review-export','--run-id',run,'--output',str(target)])
    assert result.exit_code==0 and os.stat(target).st_mode&0o777==0o600
    packet=json.loads(target.read_text());assert all(d['decision']=='pending' for d in packet['approval']['decisions'].values())
    result=runner.invoke(args=['archive-publish','--run-id',run,'--review',str(target)])
    assert result.exit_code==1 and read_snapshot(database) is None
    packet['approval']=approval(c);target.write_text(json.dumps(packet))
    assert runner.invoke(args=['archive-publish','--run-id',run,'--review',str(target)]).exit_code==0
    assert runner.invoke(args=['archive-review-export','--run-id',run,'--output',str(target)]).exit_code==1


def test_cli_records_failed_import_without_overwriting_archive(database,tmp_path,monkeypatch):
    run,c=staged(database);publish_run(database,run,approval(c));before=read_snapshot(database)['snapshot_id']
    path=tmp_path/'rules.json';path.write_text(json.dumps(policy_data()))
    app=create_app({'TESTING':True,'ARCHIVE_DATABASE':database,'LSF_BASE_URL':'https://example.invalid/start',
                    'LSF_ID_PARAMETER':'record','LSF_ID_NAMESPACE':'FIKTIV'})
    def failed(*a,**k):raise DetailImportError('Kalenderimport abgebrochen; Quelle oder Struktur ungeklärt.')
    monkeypatch.setattr('backend.archive_cli.run_calendar_import',failed)
    result=app.test_cli_runner().invoke(args=['source-calendar-import','--query','Fiktiv','--policy',str(path)])
    assert result.exit_code==1 and history(database)[0]['status']=='failed'
    assert 'example.invalid' not in result.output and read_snapshot(database)['snapshot_id']==before


def test_room_label_alias_only_matches_existing_detail_code():
    c=candidate(observed=[observation(room='Fiktive Raumbezeichnung -DEMO-RAUM')])
    assert not c['hard_blockers'] and any(r['code']=='room_labels' for r in c['reviews'])
    assert candidate(observed=[observation(room='Fiktive Raumbezeichnung -ANDERER-RAUM')])['hard_blockers']


def test_changed_snapshot_has_history_and_old_snapshot_remains_available(database):
    run,c=staged(database);first=publish_run(database,run,approval(c))
    changed=course_detail();course=replace(changed.source_course,title='Fiktiver geänderter Titel')
    changed=replace(changed,source_course=course)
    run2,c2=staged(database,candidate(changed));second=publish_run(database,run2,approval(c2))
    assert first['snapshot_id']!=second['snapshot_id']
    assert read_snapshot(database)['events'][0]['title']=='Fiktiver geänderter Titel'
    assert read_snapshot(database,first['snapshot_id'])['events'][0]['title']!=read_snapshot(database)['events'][0]['title']


def test_partial_source_inventory_cannot_be_approved():
    report=audit();report['all_requested_weeks_observed']=False
    c=candidate(report=report)
    with pytest.raises(DetailImportError):validate_review(c,approval(c))


def test_empty_missing_backup_does_not_create_source_or_destination(tmp_path):
    source=tmp_path/'missing.sqlite';target=tmp_path/'destination.sqlite'
    with pytest.raises(DetailImportError):backup_archive(str(source),str(target))
    assert not source.exists() and not target.exists()


def test_import_driver_connects_week_fields_and_detail_inventory(monkeypatch):
    d=course_detail();refs=references((d,));sample=DetailSample(1,1,(d,))
    def fake(client,**kwargs):
        assert kwargs['start']==date(2026,12,28) and kwargs['end']==date(2027,1,10)
        assert kwargs['details'] is True and kwargs.get('requested') is None
        kwargs['on_observed_week'](SourceDocument(grid_html(),'https://example.invalid/view'),WeekResult(2026,53,'ok'))
        # Den gelesenen künstlichen Schlüssel an das Detail anbinden.
        kwargs['on_details'](refs,sample)
        return audit()
    monkeypatch.setattr('backend.importer.calendar.run_view_comparison',fake)
    monkeypatch.setattr('backend.importer.calendar.read_week_occurrences',lambda *a,**k:(observation(),))
    with SourceClient('https://example.invalid/start') as client:
        c=run_calendar_import(client,query='Fiktiv',policy=parse_policy(policy_data()),identity_policy=POLICY)
    assert not c['hard_blockers'] and c['events']


def test_json_input_rejects_duplicate_keys_and_nonfinite_numbers(tmp_path):
    from backend.archive_cli import read_json
    target=tmp_path/'input.json'
    for raw in ('{"schema":1,"schema":2}', '{"value":NaN}'):
        target.write_text(raw)
        with pytest.raises(DetailImportError):read_json(target)


@pytest.mark.parametrize('note',['Begrüßung Musterperson/Beispielname', 'Einführungen studentischer Initiativen'])
def test_welcome_labels_normalize_without_removing_review(note):
    d=course_detail(note=note)
    assert d.preview is not None
    assert d.preview.series_annotations[0].kind=='welcome_label'
    assert 'welcome_note_requires_review' in d.preview.review_reasons
    assert any(r['code']=='course_notes' for r in candidate(d)['reviews'])


@pytest.mark.parametrize('note',['Begrüßung um 12:00 Uhr', 'Begrüßung entfällt', 'Begrüßung Entfällt', 'Begrüßung Verschoben',
                                  'Einführungen studentischer Initiativen verschoben'])
def test_extended_welcome_instructions_are_still_blocked(note):
    assert course_detail(note=note).preview is None


def test_room_code_with_own_description_is_not_shortened():
    d=course_detail();original=replace(d.source_course.series[0],room='DEMO-RAUM - Fiktiver Zusatz')
    course=replace(d.source_course,series=(original,));d=replace(d,source_course=course)
    c=candidate(d,observed=[observation(room='Fiktive Raumart -DEMO-RAUM - Fiktiver Zusatz')])
    assert not c['hard_blockers'] and c['events'][0]['room']=='DEMO-RAUM - Fiktiver Zusatz'


def test_failed_publication_transaction_rolls_back_new_snapshot_and_head(database):
    run,c=staged(database);first=publish_run(database,run,approval(c))
    d=course_detail();d=replace(d,source_course=replace(d.source_course,title='Fiktiver neuer Stand'))
    run2,c2=staged(database,candidate(d))
    with sqlite3.connect(database) as db:
        db.execute("CREATE TRIGGER block_head BEFORE UPDATE ON heads BEGIN SELECT RAISE(ABORT,'Fiktiver Fehler'); END")
    with pytest.raises(DetailImportError):publish_run(database,run2,approval(c2))
    assert read_snapshot(database)['snapshot_id']==first['snapshot_id']
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT count(*) FROM snapshots').fetchone()[0]==1
        assert db.execute('SELECT status FROM runs WHERE id=?',(run2,)).fetchone()[0]=='provisional'


def test_changed_exported_review_packet_cannot_publish(database,tmp_path):
    run,c=staged(database);packet={'candidate':c,'approval':approval(c)}
    packet['candidate']['events'][0]['title']='Fiktive Manipulation'
    path=tmp_path/'changed.review.json';path.write_text(json.dumps(packet))
    result=create_app({'TESTING':True,'ARCHIVE_DATABASE':database}).test_cli_runner().invoke(
        args=['archive-publish','--run-id',run,'--review',str(path)])
    assert result.exit_code==1 and read_snapshot(database) is None


def test_table_rowspan_is_clamped_at_end_as_in_html_table_model():
    with SourceClient('https://example.invalid/start') as client:
        result=read_week_occurrences(client,SourceDocument(grid_html(rowspan=20),'https://example.invalid/view'),
                                    WeekResult(2026,53,'ok'),identity_policy=POLICY)
    assert result[0].local_date=='2026-12-28'


def test_cli_success_stages_an_unpublished_candidate(database,tmp_path,monkeypatch):
    path=tmp_path/'policy.json';path.write_text(json.dumps(policy_data()))
    c=candidate()
    monkeypatch.setattr('backend.archive_cli.run_calendar_import',lambda *a,**k:c)
    app=create_app({'TESTING':True,'ARCHIVE_DATABASE':database,'LSF_BASE_URL':'https://example.invalid/start',
                    'LSF_ID_PARAMETER':'record','LSF_ID_NAMESPACE':'FIKTIV'})
    result=app.test_cli_runner().invoke(args=['source-calendar-import','--query','Fiktiv','--policy',str(path)])
    assert result.exit_code==1
    report=json.loads(result.output)
    assert report['status']=='provisional' and not report['published']
    assert get_candidate(database,report['run_id'])==c and read_snapshot(database) is None
    for secret in ('example.invalid','FIKTIV','Lehrperson','Fiktives Studium'):
        assert secret not in result.output


def test_restore_command_uses_new_file_and_does_not_touch_active_archive(database,tmp_path):
    run,c=staged(database);publish_run(database,run,approval(c))
    runner=create_app({'TESTING':True,'ARCHIVE_DATABASE':database}).test_cli_runner()
    backup=tmp_path/'backup.sqlite';restored=tmp_path/'restored.sqlite'
    assert runner.invoke(args=['archive-backup','--output',str(backup)]).exit_code==0
    assert runner.invoke(args=['archive-restore','--input',str(backup),'--output',str(restored)]).exit_code==0
    assert read_snapshot(str(restored))==read_snapshot(database)
    assert runner.invoke(args=['archive-restore','--input',str(backup),'--output',database]).exit_code==1


def test_future_schema_version_is_never_downgraded(database):
    with sqlite3.connect(database) as db:db.execute('PRAGMA user_version=99')
    with pytest.raises(DetailImportError):begin_run(database,policy_data())
    with sqlite3.connect(database) as db:assert db.execute('PRAGMA user_version').fetchone()[0]==99


def test_planblock_text_does_not_persist_embedded_addresses():
    html=grid_html().replace('FIKTIVE GRUPPE','DEMO https://example.invalid/private')
    with SourceClient('https://example.invalid/start') as client:
        events=read_week_occurrences(client,SourceDocument(html,'https://example.invalid/view'),
                                    WeekResult(2026,53,'ok'),identity_policy=POLICY)
    assert events[0].supplementary_text=='DEMO [Adresse entfernt]'
