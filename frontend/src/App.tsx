import { APIProvider, Map } from '@vis.gl/react-google-maps';
import './App.css';

function App() {
  const API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

  if (!API_KEY) {
    return <div>No API key found, place the key in .env.local file</div>;
  }

  return (
    <APIProvider apiKey={API_KEY}>
      <div className="app-container">

        <aside className="sidebar">
          <h1>Trip planner</h1>
          <button>Calculate route</button>
        </aside>

        <main className="map-container">
          <Map
            defaultZoom={13}
            defaultCenter={{ lat: 52.2297, lng: 21.0122 }}
            mapId="DEMO_MAP_ID"
          />
        </main>

      </div>
    </APIProvider>
  );
}

export default App;