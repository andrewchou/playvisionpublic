# Setup instructions:

### Demo
    CONDA_ENV_NAME=playvision
    conda create -n $CONDA_ENV_NAME python=3.7 -y
    conda activate $CONDA_ENV_NAME
    conda install numpy opencv
    python demo/visualize_dataset.py --dataset <match_filename.json>

