set -x;

#cp -r garjus_download_rp.txt/* garjus_download_wbet_rtaREST.nii.gz/

# Rename file temporarily by adding "s" suffix, so it matches expected names in covarproc.m
# Gunzip
# Run matlab
# Rename to remove "s" suffix from input and output
# Gzip
for ASSESSOR in /nobackup/h_taylor/REMBRANDT_fmri_rest_alternate/garjus_download_wbet_rtaREST.nii.gz/Baseline/*;do
	echo $ASSESSOR;
	gunzip $ASSESSOR/PREPROC/*nii.gz;
	mv $ASSESSOR/PREPROC/wbet_rtaREST.nii $ASSESSOR/PREPROC/swbet_rtaREST.nii;
	singularity exec -B $ASSESSOR:/OUTPUTS /data/mcr/centos7/singularity/fmri_rest_v4.sif bash -c "/opt/covarproc_standalone/run_covarproc.sh /opt/mcr/v92";
	mv $ASSESSOR/PREPROC/swbet_rtaREST.nii $ASSESSOR/PREPROC/wbet_rtaREST.nii;
	mv $ASSESSOR/PREPROC/swbet_rtaREST_spm_res_bpf.nii $ASSESSOR/PREPROC/wbet_rtaREST_spm_res_bpf.nii;
	gzip $ASSESSOR/*.nii;
done
