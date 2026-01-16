# Clear log files with UTF-8 encoding (no BOM)
[System.IO.File]::WriteAllText("C:\Users\alexs\projects\sred\backend\logs\app.log", "", [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText("C:\Users\alexs\projects\sred\backend\logs\error.log", "", [System.Text.UTF8Encoding]::new($false))

venv/Scripts/python.exe -m uvicorn app.main:app --reload

# python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000