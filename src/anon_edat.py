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
# Xnatdownload -p REMBRANDT -d REMBRANDT_EDAT -s fMRI_MSIT --rs EDAT
# Outputs are in root of input dir
# OUTFILE = SESSIONID_MSIT_edat2tab.txt


DROP_COLUMNS = [
    'Subject',
    'Session',
    'Clock.Information',
    'SessionDate',
    'SessionStartDateTimeUtc',
    'DataFile.Basename',
    'RandomSeed',
]


def load_edat_date(filename):
    return read_edat(filename).SessionDate.iloc[0]


def get_edat_date(row):
    f = f'{row.ROOTDIR}/{row.SUBJECT}/{row.SESSION}/{row.SCAN}/EDAT/{row.EDAT}'
    row['EDATDATE'] = load_edat_date(f)
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

            if len(edats) == 0:
                print(f'{subj}:{sess}:{scan}:NO EDATS')
                continue
            elif len(scans) > 1:
                print(f'{subj}:{sess}:{scan}:MULTIPLE EDATS')
                continue

            edat = edats[0]
            records.append({'SUBJECT': subj, 'SESSION': sess, 'SCAN': scan, 'EDAT': edat})

    return records


def anon_dir(rootdir):
    #print(f'loading edats:{rootdir}')
    records = load_dir(rootdir)
    df = pd.DataFrame(records).sort_values(by=['SESSION'])
    df['ROOTDIR'] = rootdir
    #print('loading scans from XNAT')
    scans = Garjus().scans(projects=['REMBRANDT'])
    df = pd.DataFrame.merge(df, scans[['SESSION', 'DATE']].drop_duplicates(), left_on='SESSION', right_on='SESSION')
    #print('loading edat dates')
    df = df.apply(get_edat_date, axis=1)
    df.EDATDATE = pd.to_datetime(df.EDATDATE, format='mixed')
    df['DATEDIFF'] = (df.DATE - df.EDATDATE)
    df = df[df.DATEDIFF == '0 days']
    #print('loading link table without shifted dates')
    linked = Garjus().load_linked('REMBRANDT', delete_dates=True).dropna()
    df = pd.merge(df, linked, left_on='SUBJECT', right_on='ID').drop(columns=['ID'])
    df['anon_session'] = df['anon_id'] + df['SESSION'].str[-1]
    #print('anon each file')
    for i, row in df.iterrows():
        ifile = f'{rootdir}/{row.SUBJECT}/{row.SESSION}/{row.SCAN}/EDAT/{row.EDAT}'
        ofile = f'{rootdir}/{row.anon_session}_MSIT_edat2tab.txt'
        anon_edat(ifile, ofile)

if __name__ == "__main__":
    import sys
    anon_dir(sys.argv[1])
