
echo subject,session,mask_ICV_auto > /OUTPUTS/stats.csv

cd /INPUTS

for i in *;do 
	cd /INPUTS/${i};

	for j in *;do

		VOL=`/REPO/ext/fslstats /INPUTS/$i/$j/*/*/*/mask*.nii.gz -V | awk '{print $2}'`

		echo "$i,$j,$VOL" >> /OUTPUTS/stats.csv

	done
done
