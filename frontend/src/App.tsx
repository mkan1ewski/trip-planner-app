/// <reference types="@types/google.maps" />

import { useState } from "react";
import { APIProvider, Map } from "@vis.gl/react-google-maps";
import { PlaceAutocomplete } from "./PlaceAutocomplete";
import axios from "axios";
import "./App.css";

interface TripPlace {
  id: string;
  name: string;
  lat: number;
  lng: number;
  minDuration: number;
  maxDuration: number;
  visitTimeWindowStart: string;
  visitTimeWindowEnd: string;
  openingHours?: any;
}

function App() {
  const API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  const BACKEND_URL =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

  const [placesList, setPlacesList] = useState<TripPlace[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const [startLocationId, setStartLocationId] = useState<string | null>(null);
  const [tripStartTime, setTripStartTime] = useState<string>("09:00");
  const [tripEndTime, setTripEndTime] = useState<string>("");

  if (!API_KEY) return <div>No API key</div>;

  const handlePlaceSelect = (place: google.maps.places.PlaceResult | null) => {
    if (place && place.geometry && place.geometry.location) {
      const newPlace: TripPlace = {
        id: place.place_id || Math.random().toString(),
        name: place.name || "Unknown Place",
        lat: place.geometry.location.lat(),
        lng: place.geometry.location.lng(),
        minDuration: 60,
        maxDuration: 120,
        visitTimeWindowStart: "",
        visitTimeWindowEnd: "",
        openingHours: place.opening_hours,
      };

      setPlacesList((prevList) => {
        const newList = [...prevList, newPlace];
        if (newList.length === 1) {
          setStartLocationId(newPlace.id);
        }
        return newList;
      });
    }
  };

  const handlePlaceChange = (id: string, field: keyof TripPlace, value: any) => {
    setPlacesList((prevList) =>
      prevList.map((place) =>
        place.id === id ? { ...place, [field]: value } : place,
      ),
    );
  };

  const handleCalculateRoute = async () => {
    if (placesList.length < 2) {
      alert("Please add at least 2 places to calculate a route!");
      return;
    }

    const requestPayload = {
      trip_start_location_id: startLocationId || null,
      trip_start_time: tripStartTime || null,
      trip_end_time: tripEndTime || null,
      trip_points: placesList.map((place) => ({
        location_id: place.id,
        location_name: place.name,
        min_duration_minutes: place.minDuration,
        max_duration_minutes: place.maxDuration,
        time_window_start: place.visitTimeWindowStart || null,
        time_window_end: place.visitTimeWindowEnd || null,
        coordinates: {
          latitude: place.lat,
          longitude: place.lng,
        },
        opening_hours: place.openingHours,
      })),
    };

    try {
      setIsLoading(true);

      const response = await axios.post(
        `${BACKEND_URL}/api/calculate`,
        requestPayload,
      );

      // TODO
    } catch (error) {
      alert("Error connecting to the backend.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <APIProvider apiKey={API_KEY}>
      <div className="app-container">
        <aside className="sidebar">
          <h1>Trip Planner</h1>

          <div className="trip-settings">
            <h3>General Settings:</h3>
            <div className="time-settings-row">
              <div className="setting-row">
                <label>Start Time:</label>
                <input
                  type="time"
                  className="time-input"
                  value={tripStartTime}
                  onChange={(e) => setTripStartTime(e.target.value)}
                />
              </div>
              <div className="setting-row">
                <label>End Time (Optional):</label>
                <input
                  type="time"
                  className="time-input"
                  value={tripEndTime}
                  onChange={(e) => setTripEndTime(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="add-place-section">
            <h3>Add Places to Visit:</h3>
            <PlaceAutocomplete onPlaceSelect={handlePlaceSelect} />
          </div>

          <div className="places-list-container">
            <h3>Selected Places:</h3>

            {placesList.length === 0 ? (
              <p className="empty-list-text">
                No places added yet. Search above!
              </p>
            ) : (
              <ul className="places-list">
                {placesList.map((p, index) => (
                  <li key={p.id} className={`place-item ${startLocationId === p.id ? 'is-start' : ''}`}>
                    <div className="place-header">
                      <span className="place-name">
                        <strong>{index + 1}.</strong> {p.name}
                      </span>
                      <label className={`start-location-radio ${startLocationId === p.id ? 'active' : ''}`} title="Set as start location">
                        <input
                           type="radio"
                           name="startLocation"
                           checked={startLocationId === p.id}
                           onChange={() => setStartLocationId(p.id)}
                        />
                        Start
                      </label>
                    </div>

                    <div className="place-settings">
                      <div className="setting-row">
                        <label>Time to spend (minutes):</label>
                        <div className="range-inputs">
                          <input
                            type="number"
                            min="1"
                            className="duration-input"
                            value={p.minDuration}
                            onChange={(e) =>
                              handlePlaceChange(p.id, "minDuration", parseInt(e.target.value) || 0)
                            }
                            placeholder="Min"
                          />
                          <span> - </span>
                          <input
                            type="number"
                            min="1"
                            className="duration-input"
                            value={p.maxDuration}
                            onChange={(e) =>
                              handlePlaceChange(p.id, "maxDuration", parseInt(e.target.value) || 0)
                            }
                            placeholder="Max"
                          />
                        </div>
                      </div>

                      <div className="setting-row">
                        <label>Preferred visit time window:</label>
                        <div className="range-inputs">
                          <input
                            type="time"
                            className="time-input"
                            value={p.visitTimeWindowStart}
                            onChange={(e) =>
                              handlePlaceChange(p.id, "visitTimeWindowStart", e.target.value)
                            }
                          />
                          <span> - </span>
                          <input
                            type="time"
                            className="time-input"
                            value={p.visitTimeWindowEnd}
                            onChange={(e) =>
                              handlePlaceChange(p.id, "visitTimeWindowEnd", e.target.value)
                            }
                          />
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <button
            className="calc-button"
            onClick={handleCalculateRoute}
            disabled={isLoading}
            style={{ opacity: isLoading ? 0.7 : 1 }}
          >
            {isLoading ? "Calculating..." : "Calculate Route"}
          </button>
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
