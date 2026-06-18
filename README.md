# Santiago Ride Comparer (Uber vs. DiDi)

Santiago Ride Comparer is a lightweight, responsive Flask web application that compares Uber and DiDi tariffs in Santiago de Chile at the exact moment of request. 

The application automatically checks live variables—such as real-time travel routing, the local time of day, and live weather conditions (detecting if it is currently raining in Santiago)—to simulate and calculate accurate upfront tariffs for each ride-hailing platform.

---

## 🌟 Features

*   **Interactive Geocoding & Routing**: Look up any two points within Santiago (e.g. *Costanera Center* to *Aeropuerto de Santiago*) using OpenStreetMap Nominatim and OSRM to generate the actual driving route details.
*   **Live Route Visualization**: Render the calculated route line dynamically on a beautiful dark-mode interactive map built with **Leaflet.js**.
*   **Automatic Moment-Based Surge Calculation**:
    *   **Time-Based Surge**: Automatically checks local Santiago time to see if it is a weekday morning/evening rush hour or late night.
    *   **Weather-Based Surge**: Queries the **Open-Meteo API** to check live precipitation levels in Santiago and apply corresponding multipliers when raining.
*   **Side-by-Side Comparison**: Highlights the cheapest ride option between Uber (UberX & Comfort) and DiDi (Express & Taxi) using distinct color-coded borders and a "Cheapest" badge.

---

## 🛠️ Technology Stack

*   **Backend**: Python, Flask, requests, pytz
*   **Frontend**: Vanilla HTML5, CSS3 (Custom Glassmorphism styling), Vanilla JavaScript
*   **Maps & Routing**: Leaflet.js, OpenStreetMap Nominatim API, Project OSRM Routing API
*   **Weather**: Open-Meteo API (Free, no API key required)

---

## 🧮 Tariff Formulas (CLP)

The fare calculation utilizes baseline rates for Santiago de Chile using the formula:

$$\text{Fare} = (\text{Base Fare} + (\text{Distance} \times \text{Per KM Rate}) + (\text{Duration} \times \text{Per Minute Rate})) \times \text{Surge Multiplier}$$

### Platform Constants

| Platform & Tier | Base Fare (CLP) | Per KM Rate (CLP) | Per Min Rate (CLP) | Minimum Fare (CLP) |
| :--- | :---: | :---: | :---: | :---: |
| 🚗 **UberX** | $\$700$ | $\$250$ | $\$120$ | $\$1,400$ |
| 💎 **Uber Comfort** | $\$1,000$ | $\$320$ | $\$150$ | $\$2,000$ |
| 🧡 **DiDi Express** | $\$600$ | $\$220$ | $\$100$ | $\$1,200$ |
| 🚕 **DiDi Taxi** | $\$800$ | $\$260$ | $\$130$ | $\$1,500$ |

### Dynamic Surge Multiplier Configuration
Starting from a base multiplier of **$1.0\text{x}$**, the backend adjusts the multiplier dynamically:
*   **Morning Rush** (Mon-Fri 07:30 - 09:30): **$+0.45\text{x}$**
*   **Evening Rush** (Mon-Fri 17:30 - 20:00): **$+0.55\text{x}$**
*   **Late Night** (Daily 23:00 - 05:00): **$+0.30\text{x}$**
*   **Precipitation (Raining)**: **$+0.40\text{x}$**

---

## 🚀 Installation & Setup

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/fseoanem/ride-comparer.git
    cd ride-comparer
    ```

2.  **Install Dependencies**:
    ```bash
    pip install flask requests pytz
    ```

3.  **Run the Server**:
    ```bash
    python app.py
    ```

4.  **Access the Application**:
    Open your browser and navigate to `http://127.0.0.1:5000`.

---

## 📁 Project Structure

```
├── static/
│   ├── css/
│   │   └── style.css      # Custom dark UI stylesheet
│   └── js/
│       └── app.js         # Leaflet routing map & frontend controller
├── templates/
│   └── index.html         # Main dashboard layout template
├── app.py                 # Flask server backend (geocoding, weather, and fare math)
└── README.md              # Project documentation
```

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
