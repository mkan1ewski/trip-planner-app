/// <reference types="@types/google.maps" />

import { useState } from "react";
import {
  APIProvider,
  Map,
  Marker,
  Polyline,
  AdvancedMarker,
} from "@vis.gl/react-google-maps";
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
  rating?: number;
}

interface RouteSegment {
  from_location_id: string;
  to_location_id: string;
  travel_mode: string;
  travel_duration_seconds: number;
  distance_meters: number;
}

function App() {
  const API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  const BACKEND_URL =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

  const [placesList, setPlacesList] = useState<TripPlace[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const getCurrentDateTimeLocal = () => {
    const now = new Date();

    const offset = now.getTimezoneOffset();
    const local = new Date(now.getTime() - offset * 60 * 1000);

    return local.toISOString().slice(0, 16);
  };

  const [startLocationId, setStartLocationId] = useState<string | null>(null);
  const [tripStartTime, setTripStartTime] = useState<string>(getCurrentDateTimeLocal());
  const [tripEndTime, setTripEndTime] = useState<string>("");
  const [travelMode, setTravelMode] = useState('DRIVE');
  const [routeSegments, setRouteSegments] = useState<RouteSegment[]>([]);
  const [directionsRoutes, setDirectionsRoutes] = useState<any[]>([]);
  const [totalDurationSeconds, setTotalDurationSeconds] = useState<number>(0);

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
        rating: place.rating,
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

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    return `${hours}h ${minutes}min`;
  };

  const getSegmentColor = (mode: string) => {
    switch (mode) {
      case "DRIVE":
        return "#e53935";

      case "TRANSIT":
        return "#1e88e5";

      case "WALK":
        return "#43a047";

      default:
        return "#757575";
    }
  };

  const getGoogleTravelMode = (
    mode: string,
  ): google.maps.TravelMode => {

    switch (mode) {

      case "DRIVE":
        return google.maps.TravelMode.DRIVING;

      case "WALK":
        return google.maps.TravelMode.WALKING;

      case "TRANSIT":
        return google.maps.TravelMode.TRANSIT;

      default:
        return google.maps.TravelMode.DRIVING;
    }
  };

  const fetchDirectionsRoutes = async (
    segments: RouteSegment[],
  ) => {

    const service =
      new google.maps.DirectionsService();

    const routes = await Promise.all(
      segments.map(async (segment) => {

        const fromPlace = placesList.find(
          (p) =>
            p.id === segment.from_location_id
        );

        const toPlace = placesList.find(
          (p) =>
            p.id === segment.to_location_id
        );

        if (!fromPlace || !toPlace) {
          return null;
        }

        const result =
          await new Promise<
            google.maps.DirectionsResult
          >((resolve, reject) => {

            service.route(
              {
                origin: {
                  lat: fromPlace.lat,
                  lng: fromPlace.lng,
                },
                destination: {
                  lat: toPlace.lat,
                  lng: toPlace.lng,
                },
                travelMode:
                  getGoogleTravelMode(segment.travel_mode)
              },
              (result, status) => {

                if (
                  status === "OK"
                  && result
                ) {
                  resolve(result);
                } else {
                  reject(status);
                }
              },
            );
          });

        return {
          segment,
          route: result.routes[0],
        };
      }),
    );

    setDirectionsRoutes(
      routes.filter(Boolean),
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
      travel_mode: travelMode,
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
        rating: place.rating,
      })),
    };

    try {
      setIsLoading(true);

      const response = await axios.post(
        `${BACKEND_URL}/api/calculate`,
        requestPayload,
      );

      // setRouteSegments(response.data.route_segments || []);
      const segments =
        response.data.route_segments || [];

      setRouteSegments(segments);

      await fetchDirectionsRoutes(
        segments,
      );
      setTotalDurationSeconds(
        response.data.total_duration_seconds || 0
      );

    } catch (error) {
      alert("Error connecting to the backend.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemovePlace = (id: string) => {
    setPlacesList((prevList) =>
      prevList.filter((place) => place.id !== id)
    );

    if (startLocationId === id) {
      setStartLocationId(null);
    }

    setRouteSegments([]);
  };

  const orderedPlaces = routeSegments
    .map((segment, index) => {
      if (index === 0) {
        return [
          placesList.find(
            (p) =>
              p.id === segment.from_location_id
          ),
          placesList.find(
            (p) =>
              p.id === segment.to_location_id
          ),
        ];
      }

      return placesList.find(
        (p) =>
          p.id === segment.to_location_id
      );
    })
    .flat()
    .filter(Boolean) as TripPlace[];

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
                  type="datetime-local"
                  className="time-input"
                  value={tripStartTime}
                  onChange={(e) => setTripStartTime(e.target.value)}
                />
              </div>
              <div className="setting-row">
                <label>End Time (Optional):</label>
                <input
                  type="datetime-local"
                  className="time-input"
                  value={tripEndTime}
                  onChange={(e) => setTripEndTime(e.target.value)}
                />
              </div>
            </div>

            <div className="travel-mode-section">
              <label>Travel Mode:</label>

              <div className="travel-mode-toggles">
                <button
                  type="button"
                  className={`mode-toggle ${travelMode === 'DRIVE' ? 'active' : ''}`}
                  onClick={() => setTravelMode('DRIVE')}
                >
                  🚗 Car
                </button>

                <button
                  type="button"
                  className={`mode-toggle ${travelMode === 'TRANSIT' ? 'active' : ''}`}
                  onClick={() => setTravelMode('TRANSIT')}
                >
                  🚌 Transit
                </button>

                <button
                  type="button"
                  className={`mode-toggle ${travelMode === 'WALK' ? 'active' : ''}`}
                  onClick={() => setTravelMode('WALK')}
                >
                  🚶 Walk
                </button>
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
                      <div className="place-header-left">
                        <span className="place-name">
                          <strong>{index + 1}.</strong> {p.name}
                        </span>
                      </div>
                      <div className="place-actions">
                        <label
                          className={`start-location-radio ${
                            startLocationId === p.id ? "active" : ""
                          }`}
                          title="Set as start location"
                        >
                          <input
                            type="radio"
                            name="startLocation"
                            checked={startLocationId === p.id}
                            onChange={() => setStartLocationId(p.id)}
                          />
                          Start
                        </label>
                        <button
                          type="button"
                          className="remove-place-button"
                          onClick={() => handleRemovePlace(p.id)}
                        >
                          ✕
                        </button>
                      </div>
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

          {totalDurationSeconds > 0 && (
            <div className="route-summary">
              <div className="route-summary-title">
                Route Summary
              </div>

              <div className="route-summary-row">
                <span>Total duration:</span>

                <span className="route-summary-value">
                  {formatDuration(totalDurationSeconds)}
                </span>
              </div>
            </div>
          )}
        </aside>

        <main className="map-container">
          <Map
            defaultZoom={13}
            defaultCenter={{ lat: 52.2297, lng: 21.0122 }}
            mapId="DEMO_MAP_ID"
          >
            {orderedPlaces.map((place, index) => (
              <Marker
                key={place.id}
                position={{
                  lat: place.lat,
                  lng: place.lng,
                }}
                label={`${index + 1}`}
              />
            ))}

            {routeSegments.map((segment, index) => {

            const fromPlace = placesList.find(
              (p) =>
                p.id === segment.from_location_id
            );

            const toPlace = placesList.find(
              (p) =>
                p.id === segment.to_location_id
            );

            if (!fromPlace || !toPlace) {
              return null;
            }

            const midLat =
              (fromPlace.lat + toPlace.lat) / 2;

            const midLng =
              (fromPlace.lng + toPlace.lng) / 2;

            return (
              <>
                {/* <Polyline
                  key={`${segment.from_location_id}-${segment.to_location_id}`}
                  path={[
                    {
                      lat: fromPlace.lat,
                      lng: fromPlace.lng,
                    },
                    {
                      lat: toPlace.lat,
                      lng: toPlace.lng,
                    },
                  ]}
                  strokeColor={getSegmentColor(
                    segment.travel_mode
                  )}
                  strokeOpacity={1.0}
                  strokeWeight={5}
                /> */}
                {directionsRoutes.map(
                  (directionData, index) => {

                    const path =
                      directionData.route.overview_path.map(
                        (point: google.maps.LatLng) => ({
                          lat: point.lat(),
                          lng: point.lng(),
                        }),
                      );

                    const segment =
                      directionData.segment;

                    return (
                      <Polyline
                        key={index}
                        path={path}
                        strokeColor={getSegmentColor(
                          segment.travel_mode
                        )}
                        strokeOpacity={1.0}
                        strokeWeight={5}
                      />
                    );
                  },
                )}

                <AdvancedMarker
                  key={`label-${index}`}
                  position={{
                    lat: midLat,
                    lng: midLng,
                  }}
                >
                  <div
                    style={{
                      background: "white",
                      border: "1px solid #ccc",
                      borderRadius: "8px",
                      padding: "4px 8px",
                      fontSize: "12px",
                      fontWeight: "bold",
                      boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {formatDuration(
                      segment.travel_duration_seconds
                    )}
                  </div>
                </AdvancedMarker>
              </>
            );
          })}
          </Map>
        </main>
      </div>
    </APIProvider>
  );
}

export default App;