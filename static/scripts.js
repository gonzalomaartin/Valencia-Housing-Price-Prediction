// Valencia Property Price Predictor - Main Scripts

// Initialize Map centered on Valencia
var map = L.map('map').setView([39.4699, -0.3763], 13);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 18,
}).addTo(map);

// Custom marker icon
var customIcon = L.divIcon({
    className: 'custom-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
});

// Default marker at Valencia center
var marker = L.marker([39.4699, -0.3763], { icon: customIcon }).addTo(map);

// Function to reverse geocode (get address from coordinates)
function reverseGeocode(lat, lng) {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&addressdetails=1`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const address = data.display_name || `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            document.getElementById('address').value = address;
            document.getElementById('selectedAddress').textContent = address;
            
            // Update marker popup
            marker.bindPopup(`<b>Selected Location</b><br>${address}`).openPopup();
        })
        .catch(error => {
            console.error('Error getting address:', error);
            const fallbackAddress = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            document.getElementById('address').value = fallbackAddress;
            document.getElementById('selectedAddress').textContent = fallbackAddress;
        });
}

// Function to geocode (get coordinates from address)
function geocodeAddress(address) {
    const searchQuery = address + ', Valencia, Spain';
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&limit=1`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                const lat = parseFloat(data[0].lat);
                const lng = parseFloat(data[0].lon);
                const foundAddress = data[0].display_name;
                
                // Update map and marker
                map.setView([lat, lng], 16);
                marker.setLatLng([lat, lng]);
                
                // Update address
                document.getElementById('address').value = foundAddress;
                document.getElementById('selectedAddress').textContent = foundAddress;
                
                // Show popup
                marker.bindPopup(`<b>Found Location</b><br>${foundAddress}`).openPopup();
            } else {
                alert('Address not found. Please try a different search or click on the map.');
            }
        })
        .catch(error => {
            console.error('Error searching address:', error);
            alert('Error searching for address. Please try again.');
        });
}

// Search button click event
document.getElementById('searchBtn').addEventListener('click', function() {
    const address = document.getElementById('addressSearch').value.trim();
    if (address) {
        geocodeAddress(address);
    } else {
        alert('Please enter an address to search.');
    }
});

// Allow Enter key to trigger search
document.getElementById('addressSearch').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        const address = this.value.trim();
        if (address) {
            geocodeAddress(address);
        }
    }
});

// Click event to update marker position and get address
map.on('click', function(e) {
    var lat = e.latlng.lat;
    var lng = e.latlng.lng;
    
    // Update marker position
    marker.setLatLng(e.latlng);
    
    // Get address from coordinates
    reverseGeocode(lat, lng);
});

// Ensure property area doesn't exceed constructed area
// Constructed Area (m2_cons) = total built (livable + garden + terrace + etc.)
// Property Area (m2_property) = livable area only
// Therefore: m2_cons >= m2_property

document.getElementById('m2_cons').addEventListener('change', function() {
    const constructedArea = parseInt(this.value);
    const propertyAreaInput = document.getElementById('m2_property');
    const propertyArea = parseInt(propertyAreaInput.value);
    
    // If property area exceeds constructed area, reduce it
    if (!isNaN(propertyArea) && propertyArea > constructedArea) {
        propertyAreaInput.value = constructedArea;
    }
});

document.getElementById('m2_property').addEventListener('input', function() {
    const propertyArea = parseInt(this.value);
    const constructedAreaInput = document.getElementById('m2_cons');
    const constructedArea = parseInt(constructedAreaInput.value);
    
    // If property area exceeds constructed area, increase constructed area
    if (!isNaN(propertyArea) && propertyArea > constructedArea) {
        constructedAreaInput.value = propertyArea;
    }
});

// Form submission loading state
document.getElementById('propertyForm').addEventListener('submit', function() {
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.innerHTML = '⏳ Predicting...';
    submitBtn.disabled = true;
});
