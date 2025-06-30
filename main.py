from expense_analyzer_backend import create_app
from expense_analyzer_backend.config import config
import os

# Get config name from environment
config_name = os.environ.get('FLASK_ENV', 'development')

# Create app
app = create_app(config[config_name])
port = int(os.environ.get('PORT', 5001))
print("port:",port)

if __name__ == '__main__':
    # Get port from environment
    port = int(os.environ.get('PORT', 5001))
    print("port:",port)
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG']
    )