document.addEventListener("DOMContentLoaded", () => {
    // Initialize Map centered on Santiago, Chile
    const defaultCenter = [-33.4489, -70.6693]; // Santiago Centro
    const map = L.map("map").setView(defaultCenter, 12);

    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    let routeLayer = null;
    let startMarker = null;
    let endMarker = null;

    // Elements
    const compareForm = document.getElementById("compareForm");
    const btnText = document.getElementById("btnText");
    const loader = document.getElementById("loader");
    const errorBanner = document.getElementById("errorBanner");
    const errorMessage = document.getElementById("errorMessage");
    const resultsContainer = document.getElementById("resultsContainer");

    // Form inputs
    const startInput = document.getElementById("start");
    const endInput = document.getElementById("end");

    // Result value elements
    const distanceVal = document.getElementById("distanceVal");
    const durationVal = document.getElementById("durationVal");
    const surgeVal = document.getElementById("surgeVal");

    // Prices
    const uberXPrice = document.getElementById("uberXPrice");
    const uberComfortPrice = document.getElementById("uberComfortPrice");
    const didiExpressPrice = document.getElementById("didiExpressPrice");
    const didiTaxiPrice = document.getElementById("didiTaxiPrice");

    // Brand Cards
    const uberCard = document.getElementById("uberCard");
    const didiCard = document.getElementById("didiCard");
    const uberBadge = document.getElementById("uberBadge");
    const didiBadge = document.getElementById("didiBadge");

    compareForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Reset display
        errorBanner.style.display = "none";
        resultsContainer.style.display = "none";
        uberCard.classList.remove("cheaper");
        didiCard.classList.remove("cheaper");
        uberBadge.style.display = "none";
        didiBadge.style.display = "none";

        // Show loading state
        btnText.style.display = "none";
        loader.style.display = "block";

        const payload = {
            start: startInput.value.trim(),
            end: endInput.value.trim()
        };

        try {
            const response = await fetch("/api/compare", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "An unexpected error occurred.");
            }

            // Render Route and Markers on Map
            renderRoute(data);

            // Render Summary Values
            distanceVal.textContent = `${data.distance_km} km`;
            durationVal.textContent = `${data.duration_mins} min`;
            surgeVal.textContent = `${data.tariffs.surge_factor}x`;

            // Format Chilean Pesos (CLP)
            const formatCLP = (val) => {
                return new Intl.NumberFormat("es-CL", {
                    style: "currency",
                    currency: "CLP",
                    minimumFractionDigits: 0
                }).format(val);
            };

            const uX = data.tariffs.uber.uberx;
            const uC = data.tariffs.uber.comfort;
            const dE = data.tariffs.didi.express;
            const dT = data.tariffs.didi.taxi;

            uberXPrice.textContent = formatCLP(uX);
            uberComfortPrice.textContent = formatCLP(uC);
            didiExpressPrice.textContent = formatCLP(dE);
            didiTaxiPrice.textContent = formatCLP(dT);

            // Highlight Cheaper Brand (using standard/economy options: UberX vs DiDi Express)
            if (uX < dE) {
                uberCard.classList.add("cheaper");
                uberBadge.style.display = "block";
            } else if (dE < uX) {
                didiCard.classList.add("cheaper");
                didiBadge.style.display = "block";
            } else {
                // TIE - highlight both
                uberCard.classList.add("cheaper");
                didiCard.classList.add("cheaper");
            }

            resultsContainer.style.display = "flex";
            resultsContainer.scrollIntoView({ behavior: "smooth" });

        } catch (err) {
            errorMessage.textContent = err.message;
            errorBanner.style.display = "flex";
            errorBanner.scrollIntoView({ behavior: "smooth" });
        } finally {
            // Restore button state
            btnText.style.display = "block";
            loader.style.display = "none";
        }
    });

    function renderRoute(data) {
        // Clear previous layers
        if (routeLayer) map.removeLayer(routeLayer);
        if (startMarker) map.removeLayer(startMarker);
        if (endMarker) map.removeLayer(endMarker);

        const startLatLng = [data.start.lat, data.start.lon];
        const endLatLng = [data.end.lat, data.end.lon];

        // Create Icons
        const startIcon = L.divIcon({
            html: '<i class="fas fa-map-marker-alt" style="color: #10b981; font-size: 24px;"></i>',
            iconSize: [24, 24],
            iconAnchor: [12, 24],
            className: "custom-marker-icon"
        });

        const endIcon = L.divIcon({
            html: '<i class="fas fa-flag-checkered" style="color: #ef4444; font-size: 24px;"></i>',
            iconSize: [24, 24],
            iconAnchor: [12, 24],
            className: "custom-marker-icon"
        });

        // Add Markers
        startMarker = L.marker(startLatLng, { icon: startIcon })
            .addTo(map)
            .bindPopup(`<b>Start:</b> ${data.start.display_name}`);
            
        endMarker = L.marker(endLatLng, { icon: endIcon })
            .addTo(map)
            .bindPopup(`<b>Destination:</b> ${data.end.display_name}`);

        // Draw Route Geometry
        routeLayer = L.geoJSON(data.geometry, {
            style: {
                color: "#3b82f6",
                weight: 5,
                opacity: 0.85
            }
        }).addTo(map);

        // Zoom map to cover the route
        const group = new L.featureGroup([startMarker, endMarker, routeLayer]);
        map.fitBounds(group.getBounds().pad(0.15));
    }
});
