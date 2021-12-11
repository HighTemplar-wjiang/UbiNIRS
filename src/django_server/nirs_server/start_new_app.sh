# Find full path
#source ~/anaconda3/etc/profile.d/conda.sh
#conda activate nirs
python_fullpath=$(which python)
echo $python_fullpath

# Get current script path.
SCRIPT_DIR=$(readlink -f "$0")
BASE_DIR=$(dirname "$SCRIPT_DIR")

# Run django command.
$python_fullpath manage.py startapp $1 $2 --template=$3

# Touch the django file to trigger reload.
#echo "" >> ${BASE_DIR}/nirs_server/urls.py
