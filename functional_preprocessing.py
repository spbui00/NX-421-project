# Functional preprocessing (concatenation, motion correction, coregistration, smoothing)
#%%
import os, os.path as op, subprocess, numpy as np, nibabel as nib
from utils import loadFSL, fsl_reset, fsl_add, fsl_show, plot_fd_power
from nilearn.masking import compute_epi_mask
from nilearn.image import concat_imgs

#%%
#load FSL and dataset
fsldir = loadFSL()
fsl_reset()
# Note: Set SUBJECT_ROOT to your local path to the subject folder or create a symlink ~/subject101410 
SUBJECT_ROOT = ""
dataset_root = os.path.expanduser(SUBJECT_ROOT.strip() or "~/subject101410")
fmri_root = op.join(dataset_root, "fMRI")
runs = [
    op.join(fmri_root, "tfMRI_MOTOR_LR", "tfMRI_MOTOR_LR.nii"),
    op.join(fmri_root, "tfMRI_MOTOR_RL", "tfMRI_MOTOR_RL.nii"),
]
#Create output folders
outdir = op.join(dataset_root, "derivatives", "preprocessed_func")
os.makedirs(outdir, exist_ok=True)
fsl_add(runs)
fsl_show()

#Not sure if we need to remove the first few volumes like in lab 3?? if so use FSL roi

#%%
#--PART 1: Concatenation--
#Function to rescale the variance to 1 (normalize) using global variance of the brain voxels
def unit_var_rescale(run_path: str, outdir: str) -> str:
    img = nib.load(run_path)                     
    data = img.get_fdata(dtype=np.float32)        
    mask_img = compute_epi_mask(img) #build a brain mask from EPI 
    mask = mask_img.get_fdata().astype(bool)
    var_img = data.var(axis=-1) #temporal variance per voxel over time                   
    gvar = float(var_img[mask].mean()) if mask.any() else float(var_img.mean())
    gstd = np.sqrt(gvar) if gvar > 0 else 1.0 #global temporal std
    scaled = data / gstd                          
    out_path = op.join(outdir, op.splitext(op.basename(run_path))[0] + "_var1.nii.gz")
    nib.save(nib.Nifti1Image(scaled, img.affine, img.header), out_path)
    return out_path
#Normalize then concatenate 
normed = [unit_var_rescale(r, outdir) for r in runs] #normalize each run separately before concatenating
concat_out = op.join(outdir, "MOTOR_concat_var1.nii.gz")
nib.save(concat_imgs(normed), concat_out)
fsl_add(concat_out)
fsl_show()

#%%
#--PART 2: Motion Correction--
#Apply motion correction and then remove irregular volumes with high framewise displacement
mc_in = concat_out #apply motion correction to the concatenated runs
mc_out = op.join(outdir, "MOTOR_concat_mc.nii.gz")
subprocess.run([
    "mcflirt", "-in", mc_in, "-out", mc_out, 
    "-plots", "-mats", "-meanvol" ], check=True) #motion correction using mean volume as reference
fsl_add(mc_out)
fsl_show()
#%%
#Identify high-FD volumes that need to be removed (FD>threshold)
thr = 0.4
par_path = mc_out + ".par"
#Compute & plot FD on the full (unscrubbed) series ---
fd_plot_before = op.join(outdir, "fd_plot_before_removal.png")
fd_vals_before = op.join(outdir, "fd_values_before.txt")
fd_orig = plot_fd_power(
    par_path, fd_plot_before, thr=thr,
    save_values_path=fd_vals_before, return_fd=True)
#Identify outliers(FD >= threshold)
bad = np.where(fd_orig >= thr)[0]
np.savetxt(op.join(outdir, "irregular_volumes.txt"), bad, fmt="%d")
# Scrub volumes (remove outliers) and save scrubbed 4D series
img  = nib.load(mc_out)
data = img.get_fdata(dtype=np.float32)
T    = data.shape[-1]
keep = np.setdiff1d(np.arange(T), bad)
scrub_out = op.join(outdir, "MOTOR_concat_mc_scrubbed.nii.gz")
nib.save(nib.Nifti1Image(data[..., keep], img.affine, img.header), scrub_out)
# Plot FD on the scrubbed series
fd_plot_after = op.join(outdir, "fd_plot_after_removal.png")
fd_vals_after = op.join(outdir, "fd_values_after.txt")
plot_fd_power(
    par_path, fd_plot_after, thr=thr,
    keep=keep, break_gaps=True, save_values_path=fd_vals_after)
fsl_add(scrub_out)
fsl_show()

#For subsequent steps, use scrub_out as the clean 4D series

#--PART 3: Coregistration--

#--PART 4: Gaussian smoothing--

# %%
