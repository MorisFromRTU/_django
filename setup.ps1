python -m venv myenv
.\myenv\Scripts\Activate.ps1
pip install -r requirements.txt

Set-Location -Path currency

python manage.py makemigrations
python manage.py migrate