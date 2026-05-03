/// <reference types="@types/google.maps" />

import { useState } from 'react';
import { APIProvider, Map } from '@vis.gl/react-google-maps';
import { PlaceAutocomplete } from './PlaceAutocomplete';
import './App.css';

interface TripPlace {
  id: string;
  name: string;
  lat: number;
  lng: number;
}

function App() {
  const API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  const [placesList, setPlacesList] = useState<TripPlace[]>([]);

  if (!API_KEY) return <div>No API key</div>;

  const handlePlaceSelect = (place: google.maps.places.PlaceResult | null) => {
    if (place && place.geometry && place.geometry.location) {
      const newPlace: TripPlace = {
        id: place.place_id || Math.random().toString(),
        name: place.name || 'Unknown Place',
        lat: place.geometry.location.lat(),
        lng: place.geometry.location.lng(),
      };

      setPlacesList((prevList) => [...prevList, newPlace]);
    }
  };

  return (
    <APIProvider apiKey={API_KEY}>
      <div className="app-container">

        <aside className="sidebar">
          <h1>Trip Planner</h1>

          <PlaceAutocomplete onPlaceSelect={handlePlaceSelect} />

          <div className="places-list-container">
            <h3>Selected Places:</h3>

            {placesList.length === 0 ? (
              <p className="empty-list-text">No places added yet. Search above!</p>
            ) : (
              <ul className="places-list">
                {placesList.map((p, index) => (
                  <li key={p.id} className="place-item">
                    <span><strong>{index + 1}.</strong> {p.name}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <button className="calc-button">Calculate Route</button>
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