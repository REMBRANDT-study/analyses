import os
import io
import pandas as pd
from garjus import Garjus


# Load directory of EDATs into df with Subject/Session
# Get scan dates from XNAT and merge into df
# Get dates from EDAT and merge into df
# Find date mismatches and drop those for now
# Load anon IDs from REDCap
# Load each file, drop identifier columns, save with anon IDs
# Input dir is as downloaded with Xnatdownload:
# Xnatdownload -p PROJECT -d OUTPUT_DIRECTORY -s fMRI_SCANTYPE --rs EDAT
# Outputs are in root of input dir
# OUTFILE = SESSIONID_SCANTYPE_edat2tab.txt


DROP_COLUMNS = [
    'Subject',
    'Session',
    'Clock.Information',
    'SessionDate',
    'SessionStartDateTimeUtc',
    'DataFile.Basename',
    'RandomSeed',
]


def get_link():
    return pd.read_csv(io.StringIO(LINKEDLIST), sep=r'\s+', dtype=str)


def load_edat_date(filename):
    return read_edat(filename).SessionDate.iloc[0]


def get_edat_date(row):
    f = f'{row.ROOTDIR}/{row.SUBJECT}/{row.SESSION}/{row.SCAN}/EDAT/{row.EDAT}'
    try:
        row['EDATDATE'] = load_edat_date(f)
    except Exception as err:
        row['EDATDATE'] = ''

    return row


def read_edat(edat_path):
    skiprows = 0
    first_field = 'ExperimentName'
    encoding = 'utf-16'

    # Determine how many rows to skip prior to header
    try:
        with io.open(edat_path, encoding=encoding) as _f:
            for line in _f:
                if line.startswith(first_field):
                    break
                else:
                    skiprows += 1
    except UnicodeError:
        encoding = 'utf-8'
        with io.open(edat_path, encoding=encoding) as _f:
            for line in _f:
                if line.startswith(first_field):
                    break
                else:
                    skiprows += 1

    # Load Data
    return pd.read_csv(edat_path, sep='\t', encoding=encoding, skiprows=skiprows, header=0)


def anon_edat(infilename, outfilename):
    df = read_edat(infilename)

    df = df.drop(columns=DROP_COLUMNS, errors='ignore')

    # save tab-delimited
    df.to_csv(outfilename, sep='\t', index=False)


def load_dir(rootdir):
    records = [];
    subjects = os.listdir(rootdir)
    subjects = [x for x in subjects if os.path.isdir(f'{rootdir}/{x}')]
    for subj in subjects:
        sessions = os.listdir(f'{rootdir}/{subj}')
        sessions = [x for x in sessions if os.path.isdir(f'{rootdir}/{subj}/{x}')]
        for sess in sessions:
            scans = os.listdir(f'{rootdir}/{subj}/{sess}')
            scans = [x for x in scans if os.path.isdir(f'{rootdir}/{subj}/{sess}/{x}')]
            if len(scans) == 0:
                print(f'{subj}:{sess}:NO SCANS')
                continue
            elif len(scans) > 1:
                print(f'{subj}:{sess}:MULTIPLE SCANS')
                continue

            scan = scans[0]

            edats = os.listdir(f'{rootdir}/{subj}/{sess}/{scan}/EDAT')
            edats = [x for x in edats if x.endswith('tab.txt')]

            if len(edats) == 0:
                print(f'{subj}:{sess}:{scan}:NO EDATS')
                continue
            elif len(edats) > 1:
                print(f'{subj}:{sess}:{scan}:MULTIPLE EDATS')
                continue

            edat = edats[0]
            scantype = scan.split('-x-')[-2]
            records.append({'SUBJECT': subj, 'SESSION': sess, 'SCAN': scan, 'EDAT': edat, 'SCANTYPE': scantype})

    return records


def anon_dir(project, rootdir):
    print(f'loading edats:{rootdir}')
    records = load_dir(rootdir)
    df = pd.DataFrame(records).sort_values(by=['SESSION'])
    df['ROOTDIR'] = rootdir

    print(f'loaded:{len(df)}')

    print('loading scans from XNAT')
    scans = Garjus().scans(projects=[project])
    df = pd.DataFrame.merge(df, scans[['SESSION', 'DATE']].drop_duplicates(), left_on='SESSION', right_on='SESSION')

    print(f'merged:{len(df)}')

    print('drop MISSING and CONVERT_FAILED')
    df = df[df.EDAT != 'MISSING_DATA.txt']
    df = df[df.EDAT != 'CONVERT_FAILED.txt']
    df = df[df.EDAT != 'contrasts.mat']
    df = df[~df.EDAT.str.endswith('.edat2')]

    print(f'left:{len(df)}')

    print('loading edat dates')
    df = df.apply(get_edat_date, axis=1)
    df.EDATDATE = pd.to_datetime(df.EDATDATE, format='mixed')
    df['DATEDIFF'] = (df.DATE - df.EDATDATE)

    print('DATE MISMATCH:')
    print(df[df.DATEDIFF != '0 days'])
    df = df[df.DATEDIFF == '0 days']

    if False:
        print('using local linked')
        linked = get_link()
    else:
        print('loading link table without shifted dates')
        linked = Garjus().load_linked(project, delete_dates=True).dropna()

    df = pd.merge(df, linked, left_on='SUBJECT', right_on='ID').drop(columns=['ID'])
    df['anon_session'] = df['anon_id'] + df['SESSION'].str[-1]

    print(f'matched:{len(df)}')

    print('anon each file')
    count = 0
    for i, row in df.iterrows():
        ifile = f'{rootdir}/{row.SUBJECT}/{row.SESSION}/{row.SCAN}/EDAT/{row.EDAT}'
        ofile = f'{rootdir}/{row.anon_session}_{row.SCANTYPE}_edat2tab.txt'
        anon_edat(ifile, ofile)
        count += 1

    print(f'{count} files complete')

if __name__ == "__main__":
    import sys
    anon_dir(sys.argv[1], sys.argv[2])
