
echo subject,mask_ICV_auto > /OUTPUTS/stats.csv

cd /INPUTS

for i in *;do 

	VOL=`fslstats $i/*/*/*/mask*.nii.gz -V | awk '{print $2}'`

	echo "$i,$VOL" >> /OUTPUTS/stats.csv

done
