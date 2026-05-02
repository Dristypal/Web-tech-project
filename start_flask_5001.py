import os
# ensure we run from project root so imports work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# set local sqlite URL for dev
os.environ.setdefault('SQLITE_URL', 'sqlite:///instance/campusconnect.db')

from app import app

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
