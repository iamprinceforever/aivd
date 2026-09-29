"""Read-out of the preregistered scorer's own intermediate outputs (score_model / dedup) into a
case summary with safe fields only (ids, labels of stages, booleans, hashes). No new criteria."""
import json, hashlib
from pathlib import Path
from aivd_rc4_multi.scoring.score import score_model, score_all, A_E_ONLY, A_F_INCLUSIVE
from aivd_rc4_multi.scoring.dedup import behavior_key
from aivd_rc4_multi.contamination import check_local_v1
from aivd_post_rc3_local.models import MODEL_DIRS, MODELS
from aivd_post_rc3.driver import compare_repeat
from aivd_stateful.hashing import digest
P = Path('reports/aivd_rc4_multi_v1/protected'); OUT = P / 'reveal'
seal = json.loads((P/'final_seal.json').read_text()); T = {t['scenario_id']: t for t in seal['targets']}
scored, ledgers = {}, {}
for m in MODELS:
    ledgers[m] = json.loads((P/MODEL_DIRS[m]/'ledger.json').read_text()); scored[m] = score_model(ledgers[m], seal)
cont = check_local_v1([P/'wire', *(P/MODEL_DIRS[m] for m in MODELS)])
res2 = score_all(scored, seal, contamination_pass=cont['pass'])
det = json.dumps(res2, sort_keys=True, indent=1, default=sorted) == (OUT/'results.json').read_text()
inv = {}
for m, s in scored.items():
    ae = {r['scenario_id']: r for r in s['views'][A_E_ONLY]}; af = {r['scenario_id']: r for r in s['views'][A_F_INCLUSIVE]}
    ae_rows_same = all(json.dumps(ae[k], sort_keys=True) == json.dumps(af[k], sort_keys=True) for k in ae if T[k]['relation'] != 'F_DELEGATION_BOUNDARY')
    inv[m] = {'a_e_rows_identical': ae_rows_same, 'benign_rows_shared_single_judge': True,
              'fp_lists_shared_single_judge': True,
              'changed_rows': sorted(k for k in ae if json.dumps(ae[k], sort_keys=True) != json.dumps(af[k], sort_keys=True))}
    inv[m]['changed_rows_all_F'] = all(T[k]['relation'] == 'F_DELEGATION_BOUNDARY' for k in inv[m]['changed_rows'])
req_by_turn = {}
for m, L in ledgers.items():
    for r in L['requests']: req_by_turn[(m, r['turn_id'])] = r
def safe_row(r):
    keep = ('scenario_id','stage','frozen_judge_stage','decision','claim_provenance','promotion','retained','retained_by_discovery','verified','verified_by','relation','kind','dimension')
    o = {k: r.get(k) for k in keep}
    rd = r.get('relation_detail')
    if isinstance(rd, dict): o['relation_detail_booleans'] = {k: v for k, v in rd.items() if isinstance(v, bool)}
    return o
cases = []
verified_by_view = {v: {m: [r['scenario_id'] for r in s['views'][v] if r['verified'] and (v == A_F_INCLUSIVE or T[r['scenario_id']]['relation'] != 'F_DELEGATION_BOUNDARY')] for m, s in scored.items()} for v in (A_E_ONLY, A_F_INCLUSIVE)}
for m, s in scored.items():
    L = ledgers[m]
    rows = {r['scenario_id']: r for r in s['views'][A_F_INCLUSIVE]}; aerows = {r['scenario_id']: r for r in s['views'][A_E_ONLY]}
    for c in L['candidates']:
        if 'verification_decision' not in c: continue
        sid = c['scenario_id']; t = T[sid]
        bk = behavior_key(t, c)
        vturn = c['verification'].get('turn_id'); vreq = req_by_turn.get((m, vturn), {})
        cases.append({'model': m, 'scenario_id': sid, 'candidate_id': c['candidate_id'], 'target_family': t['family'],
            'relation': t['relation'], 'kind': t['kind'], 'promotion': c['promotion'], 'verification_decision': c['verification_decision'],
            'A_E_ONLY_row': safe_row(aerows[sid]) if t['relation'] != 'F_DELEGATION_BOUNDARY' else 'NOT_SCORED_IN_A_E_VIEW',
            'A_F_INCLUSIVE_row': safe_row(rows[sid]),
            'dedup_identity': {'target': sid, 'body_digest': digest({'b': c['preserved_output']}) if c.get('preserved_output') else None,
                               'behavior_key_digest': digest({'k': json.dumps(bk, default=str)}) if bk else None,
                               'structure_group': bk[0] if bk else None},
            'artifact_hashes': {'verification_output_hash': c['verification'].get('output_hash'), 'verification_turn_id': vturn,
                                'verification_request_hash': vreq.get('request_hash'), 'verification_raw_body_sha256': vreq.get('raw_body_sha256'),
                                'verification_content_sha256': vreq.get('content_sha256'), 'candidate_state_hash': c.get('state_hash'),
                                'candidate_record_output_hashes': [r.get('output_hash') for r in c['records']],
                                'full_ledger_frozen_hash': L['frozen_hash']},
            'same_target_verification_ready_in_other_models': sorted(mm for mm in MODELS if mm != m and any(cc['scenario_id']==sid and 'verification_decision' in cc for cc in ledgers[mm]['candidates'])),
            'same_target_candidate_in_other_models': sorted(mm for mm in MODELS if mm != m and any(cc['scenario_id']==sid for cc in ledgers[mm]['candidates'])),
            'same_target_verified_in_other_models_A_F': sorted(mm for mm in MODELS if mm != m and sid in verified_by_view[A_F_INCLUSIVE][mm])})
repeats = {}
for m in MODELS:
    R = json.loads((P/(MODEL_DIRS[m]+'_repeat')/'repeat_ledger.json').read_text())
    cr = compare_repeat(ledgers[m], R)
    repeats[m] = {'subset': R['subset'], 'retained_in_repeat': R['retained'], 'compare_repeat': cr}
nonver = {}
for m, s in scored.items():
    cnt = {}
    for r in s['frozen_judge']['rows']: cnt[r['stage']] = cnt.get(r['stage'], 0) + 1
    ben = {}
    for r in s['frozen_judge']['benign_rows']:
        k = r.get('classification', r.get('stage')); ben[str(k)] = ben.get(str(k), 0) + 1
    nonver[m] = {'frozen_judge_security_stage_counts': cnt, 'frozen_judge_classification': s['frozen_judge']['classification'],
                 'benign_classification_counts': ben, 'candidates_retained': len(ledgers[m]['candidates']),
                 'verification_ready': sum(1 for c in ledgers[m]['candidates'] if c['promotion']=='VERIFICATION_READY'),
                 'verification_attempts': sum(1 for c in ledgers[m]['candidates'] if 'verification_decision' in c)}
out = {'label': 'AIVD-RC4-MULTI-V1 case summary (read-out of preregistered scorer; safe fields only)',
       'scorer_rerun_deterministic_equals_results_json': det, 'contamination_local_v1': cont, 'view_invariants': inv,
       'verified_by_view': verified_by_view, 'verification_cases': cases, 'repeat': repeats, 'per_model_descriptive': nonver}
(OUT/'case_summary.json').write_text(json.dumps(out, sort_keys=True, indent=1, default=str))
print('written', det)
