#Structural preprocessing (skull stripping, tissue segmentation)
import os, os.path as op, sys, subprocess
from utils import loadFSL, fsl_reset, fsl_add, fsl_show

#Load FSL and dataset
fsldir = loadFSL()
fsl_reset()
#Note: Set SUBJECT_ROOT to your local path to the subject folder or create a symlink called ~/subject101410 that points to the folder (especially if there are spaces in your path name)
SUBJECT_ROOT = ""
dataset_root = os.path.expanduser(SUBJECT_ROOT.strip() or "~/subject101410")
t1 = os.path.join(dataset_root, "T1w", "T1w.nii.gz") 
#Create output folders for the preprocessed images
outdir = os.path.join(dataset_root, "derivatives", "preprocessed_struc")
os.makedirs(outdir, exist_ok=True)
base = op.splitext(op.splitext(op.basename(t1))[0])[0] #raw image
outbase = op.join(outdir, base + "_brain")  #BET prefix (skull stripped image)
seg_base = op.join(outdir, base + "_fast")   #FAST prefix (tissue segmented image)
fsl_add(t1)
fsl_show()

#Perform skull stripping with FSL BET
cmd = ["bet", t1, outbase, "-R", "-f", "0.35", "-g", "-0.1", "-m"] #need to find optimal mask value
res = subprocess.run(cmd, capture_output=True, text=True)
res.check_returncode()
brain = outbase + ".nii.gz"
bet_mask = outbase + "_mask.nii.gz"
fixed_mask = op.join(outdir, base + "_mask_fix.nii.gz")
fixed_brain = op.join(outdir, base + "_brain_fix.nii.gz")
subprocess.run(["fslmaths", bet_mask, "-fillh", "-dilM", "-dilM", "-ero", "-bin", fixed_mask], check=True) #need to optimize parameters
subprocess.run(["fslmaths", t1, "-mas", fixed_mask, fixed_brain], check=True)
# use the stripped brain for segmentation
brain = fixed_brain
fsl_add(brain)
fsl_show()

#Perform tissue segmentation with FSL FAST
print("Running FAST…")
cmd = ["fast", "-v", "-t", "1", "-n", "3", "-o", seg_base, brain]  # -v for debugging, also need to figure out optimal parameters
proc = subprocess.Popen(cmd)  # inherits stdout/stderr → progress prints live
ret = proc.wait()
#3a. White/grey segmentation
#pveseg = seg_base + "_pveseg.nii.gz" #labels: 0=CSF, 1=GM, 2=WM 
#launch_fsleyes(image=None, extra_args=[t1, brain, pveseg]) #display all 3 images in one overlay 
#3b. RGB segmentation
pve0 = seg_base + "_pve_0.nii.gz" #CSF
pve1 = seg_base + "_pve_1.nii.gz" #GM
pve2 = seg_base + "_pve_2.nii.gz" #WM
fsl_add(pve0, "-cm", "red",   "-dr", "0", "1", "-a", "80")   # CSF
fsl_add(pve1, "-cm", "green", "-dr", "0", "1", "-a", "80")   # GM
fsl_add(pve2, "-cm", "blue",  "-dr", "0", "1", "-a", "80")   # WM
fsl_show() 
