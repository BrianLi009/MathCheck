module load cuda gcc python/3.10

virtualenv --no-download --clear ~/alphacube_env

source ~/alphacube_env/bin/activate

pip install --no-index --upgrade pip

pip install -r requirements.txt
