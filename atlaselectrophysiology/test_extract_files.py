from atlaselectrophysiology.extract_files import extract_rmsmap
from ibllib.io import spikeglx
from pathlib import Path

ks_path = Path('/mnt/hdd1/ephys/AL41/20211027/ks_matlab')
ephys_path = Path('/mnt/hdd1/ephys/AL41/20211027/AL41_20211027_g0/AL41_20211027_g0_imec0')
out_path = Path('/mnt/hdd1/ephys/AL41/20211027/test_alf')
# extract_data(ks_path, ephys_path, out_path, duration=1850)

efiles = spikeglx.glob_ephys_files(ephys_path)
for efile in efiles:
    if efile.get('lf') and efile.lf.exists():
        extract_rmsmap(efile.lf, out_folder=out_path, duration=1850)

