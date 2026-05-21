/// <reference types="@types/google.maps" />

import { useEffect, useRef, useState } from 'react';
import { useMapsLibrary } from '@vis.gl/react-google-maps';

interface PlaceAutocompleteProps {
  onPlaceSelect: (place: google.maps.places.PlaceResult | null) => void;
}

export const PlaceAutocomplete = ({ onPlaceSelect }: PlaceAutocompleteProps) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const places = useMapsLibrary('places');
  const [autocomplete, setAutocomplete] = useState<google.maps.places.Autocomplete | null>(null);

  useEffect(() => {
    if (!places || !inputRef.current) return;

    const widget = new places.Autocomplete(inputRef.current, {
      fields: ['geometry', 'name', 'place_id', 'opening_hours', 'rating'],
    });

    setAutocomplete(widget);
  }, [places]);

  useEffect(() => {
    if (!autocomplete) return;

    const listener = autocomplete.addListener('place_changed', () => {
      const place = autocomplete.getPlace();

      if (place && place.geometry) {
        onPlaceSelect(place);

        if (inputRef.current) {
          inputRef.current.value = '';
        }
      }
    });

    return () => {
      google.maps.event.removeListener(listener);
    };
  }, [autocomplete, onPlaceSelect]);

  return (
    <div className="autocomplete-container">
      <input
        ref={inputRef}
        type="text"
        placeholder="Search for a place..."
        style={{
          width: '100%',
          padding: '12px',
          fontSize: '16px',
          border: '1px solid #ccc',
          borderRadius: '4px',
          boxSizing: 'border-box',
          marginBottom: '10px'
        }}
      />
    </div>
  );
};