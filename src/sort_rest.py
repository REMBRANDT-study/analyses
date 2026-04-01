#garjus download -p REMBRANDT -t fmri_rest_v4 -r PREPROC -f swbet_rtaREST_spm_res_bpf.nii.gz REMBRANDT -s Baseline
#garjus download -p REMBRANDT -t fmri_rest_v4 -r PREPROC -f swbet_rtaREST_spm_res_bpf.nii.gz REMBRANDT=Month8 -s Month8
#garjus download -p REMBRANDT -t fmri_rest_v4 -r PREPROC -f swbet_rtaREST_spm_res_bpf.nii.gz REMBRANDT-Month16 -s Month16
#garjus download -p REMBRANDT -t fmri_rest_v4 -r PREPROC -f swbet_rtaREST_spm_res_bpf.nii.gz REMBRANDT-Month24 -s Month24
#garjus download -p REMBRANDT -t fmri_rest_v4 -r PREPROC -f rp_taREST.txt REMBRANDT-motion

import os
from garjus import Garjus

g = Garjus()

print('loading scan data')
scans = g.scans(projects=['REMBRANDT'])
dfa = g.assessors(projects=['REMBRANDT'])
dfa = dfa[dfa['PROCTYPE'] == 'fmri_rest_v4']

def get_rest(row):
    row['REST'] = row['INPUTS'].get('scan_rest')
    return row

dfa = dfa.apply(get_rest, axis=1)

df = dfa.merge(scans[['full_path', 'SCANTYPE']], left_on='REST', right_on='full_path')

for i, row in df.iterrows():
    run = ''
    if row['SCANTYPE'] == 'fMRI_REST1':
        run = 'run1'
    elif row['SCANTYPE'] == 'fMRI_REST2':
        run = 'run2'
    else:
        continue

    assr = row['ASSR']

    print(assr, row['SESSTYPE'], run)

    sesstype = row['SESSTYPE']

    try:
        os.makedirs(f'/tmp/{sesstype}-{run}')
    except:
        pass

    src = f'/tmp/REMBRANDT-rest/{assr}'
    dst = f'/tmp/{sesstype}-{run}/{assr}'

    if os.path.exists(dst):
        print(f'already exists {dst}')
        continue
    elif not os.path.exists(src):
        print(f'does not exist:{src}')
        continue

    print(f'copying {src} to {dst}')
    cmd = f'cp -r {src} {dst}'
    print(cmd)
    os.system(cmd)
