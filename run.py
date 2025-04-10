#!/usr/bin/env python3
from webapp import create_app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Run the app on all interfaces (0.0.0.0) to make it accessible externally
    app.run(host='0.0.0.0', port=5555, debug=True)
