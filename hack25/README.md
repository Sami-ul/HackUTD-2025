# DFW Network Map Dashboard Component

A self-contained React component that displays network towers on an interactive Leaflet map centered on the Dallas-Fort Worth area.

## Features

- 🗺️ Interactive map using Leaflet (via react-leaflet)
- 📍 ~10 network tower nodes with fixed coordinates around DFW
- 🟢 Green markers for online nodes
- 🔴 Red markers for offline nodes
- 🔄 Auto-refreshes data every 5 seconds
- 📡 Fetches from `/api/nodes` with automatic fallback to mock data
- 💬 Click markers to see node details in popups
- 📱 Responsive design with Tailwind CSS
- 🎨 Clean, minimal styling

## Quick Start

1. **Install frontend dependencies:**
   ```bash
   npm install
   ```

2. **Install backend dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Flask backend** (in one terminal):
   ```bash
   python backend/app.py
   ```

4. **Start the React frontend** (in another terminal):
   ```bash
   npm run dev
   ```

5. Open your browser to `http://localhost:5173` (or the port shown by Vite)

The map will automatically connect to the Flask backend and refresh every 5 seconds!

## Installation

### Frontend
```bash
npm install
```

### Backend
```bash
pip install -r requirements.txt
```

## Development

### Frontend

Start the React development server:

```bash
npm install
npm run dev
```

### Backend (Flask)

The Flask backend stores node state and provides API endpoints to manage nodes.

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Start the Flask backend server:

```bash
cd backend
python app.py
```

Or from the root directory:

```bash
python -m backend.app
```

The Flask server will run on `http://localhost:3001` and the React app (via Vite proxy) will automatically connect to it.

### Alternative: Mock API Server

If you prefer the simple Node.js mock server instead:

```bash
node mock-api-server.js
```

Then access the app at `http://localhost:5173` (or the port shown by Vite).

## Usage

The `DFWNetworkMap` component is self-contained and can be easily embedded into any React application:

```jsx
import DFWNetworkMap from './components/DFWNetworkMap'

function App() {
  return (
    <div className="container">
      <DFWNetworkMap />
    </div>
  )
}
```

## API Endpoints

### Flask Backend

The Flask backend provides the following REST API endpoints:

- **GET `/api/nodes`** - Get all nodes with their current status
- **GET `/api/nodes/<id>`** - Get a specific node by ID
- **PUT/PATCH `/api/nodes/<id>`** - Update a node's status or other properties
  ```json
  {
    "status": "online"  // or "offline"
  }
  ```
- **POST `/api/nodes/<id>/toggle`** - Toggle a node's status between online/offline
- **GET `/api/metrics`** - Get current network health metrics
- **GET `/api/history`** - Get historical metrics data for charts (updates every minute)
- **POST `/api/metrics/publish`** - Publish new metrics data point
  ```json
  {
    "call_drops": 5,        // Optional: number of call drops
    "active_nodes": 9       // Optional: number of active nodes
  }
  ```
- **GET `/api/health`** - Health check endpoint

### Example: Update Node Status

Using curl:

```bash
# Update node 1 to offline
curl -X PUT http://localhost:3001/api/nodes/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "offline"}'

# Toggle node 2's status
curl -X POST http://localhost:3001/api/nodes/2/toggle
```

Using Python:

```python
import requests

# Update node status
response = requests.put(
    'http://localhost:3001/api/nodes/1',
    json={'status': 'offline'}
)

# Toggle node status
response = requests.post('http://localhost:3001/api/nodes/2/toggle')
```

### API Response Format

The API returns node objects in this format:

```json
[
  {
    "id": 1,
    "name": "Tower Alpha",
    "lat": 32.7767,
    "lon": -96.7970,
    "status": "online"
  }
]
```

If the API is unavailable, the React component automatically falls back to hardcoded mock data.

### Testing the API

Run the test script to verify all endpoints:

```bash
python backend/test_api.py
```

Or try the example update script:

```bash
python backend/example_update.py
```

### Publishing Metrics Data

The graph updates every minute automatically. To publish new data points manually:

```bash
python backend/example_publish_metrics.py
```

Or using curl:

```bash
# Publish call drops and active nodes
curl -X POST http://localhost:3001/api/metrics/publish \
  -H "Content-Type: application/json" \
  -d '{"call_drops": 5, "active_nodes": 9}'

# Publish only call drops (active_nodes will use current count)
curl -X POST http://localhost:3001/api/metrics/publish \
  -H "Content-Type: application/json" \
  -d '{"call_drops": 3}'
```

**Note:** The graph refreshes every 60 seconds. New data points published via the API will appear on the next refresh.

## Component Props

The component currently accepts no props and is fully self-contained. Future enhancements could include:
- Custom refresh interval
- Custom center coordinates
- Custom zoom level
- Custom node styling

## Build

```bash
npm run build
```

## Technologies

### Frontend
- React 18
- Vite
- Tailwind CSS
- Leaflet / react-leaflet

### Backend
- Flask 3.0
- flask-cors (for CORS support)
- Python 3.x

