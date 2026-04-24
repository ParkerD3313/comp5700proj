@echo off

python -m venv venv
call venv\Scripts\activate

pip install -r requirements.txt

echo Running Input-1: cis-r1.pdf and cis-r1.pdf
python main.py cis-r1.pdf cis-r1.pdf

echo Running Input-2: cis-r1.pdf and cis-r2.pdf
python main.py cis-r1.pdf cis-r2.pdf

echo Running Input-3: cis-r1.pdf and cis-r3.pdf
python main.py cis-r1.pdf cis-r3.pdf

echo Running Input-4: cis-r1.pdf and cis-r4.pdf
python main.py cis-r1.pdf cis-r4.pdf

echo Running Input-5: cis-r2.pdf and cis-r2.pdf
python main.py cis-r2.pdf cis-r2.pdf

echo Running Input-6: cis-r2.pdf and cis-r3.pdf
python main.py cis-r2.pdf cis-r3.pdf

echo Running Input-7: cis-r2.pdf and cis-r4.pdf
python main.py cis-r2.pdf cis-r4.pdf

echo Running Input-8: cis-r3.pdf and cis-r3.pdf
python main.py cis-r3.pdf cis-r3.pdf

echo Running Input-9: cis-r3.pdf and cis-r4.pdf
python main.py cis-r3.pdf cis-r4.pdf

call venv\Scripts\deactivate
echo All inputs complete.