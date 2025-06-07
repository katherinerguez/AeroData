const map = L.map('map').setView([0, 0], 2); 

// Capa base de OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',  {
    attribution: '© OpenStreetMap'
}).addTo(map);

let marker = null;

function updateLocation() {
    fetch('/get_location')
        .then(response => response.json())
        .then(data => {
            if (data_location.latitude && data_location.longitude) {
                const { icao24, latitude, longitude } = data_location;
                const position = [latitude, longitude];

                if (marker) {
                    map.removeLayer(marker);
                }

                marker = L.marker(position)
                    .addTo(map)
                    .bindPopup(`<strong>${icao24}</strong><br>Lat: ${latitude}<br>Lon: ${longitude}`)
                    .openPopup();

                map.setView(position, 6); 
            }
        })
        .catch(err => console.error('Error obteniendo localización:', err));
}

updateLocation();

setInterval(updateLocation, 10000);