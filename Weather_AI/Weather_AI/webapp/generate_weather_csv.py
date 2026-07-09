import time
import requests
import pandas as pd

try:
    import pycountry_convert as pc
except ImportError:
    raise RuntimeError(
        "Lipsește pachetul 'pycountry-convert'. Rulează: python -m pip install pycountry-convert"
    )

INPUT_FILE = "capitale_300.csv"
OUTPUT_FILE = "weather_data.csv"

START_DATE = "2025-01-01"
END_DATE = "2025-12-31"

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"

REQUEST_DELAY_SECONDS = 2.0
MAX_RETRIES = 6
MAX_CAPITALS = 120

# Capitale importante pe care vrem să le includem sigur
PRIORITY_CAPITALS = [
    "Bucharest",
    "Athens",
    "Madrid",
    "Paris",
    "Berlin",
    "Rome",
    "London",
    "Vienna",
    "Budapest",
    "Prague",
    "Warsaw",
    "Sofia",
    "Belgrade",
    "Zagreb",
    "Bratislava",
    "Lisbon",
    "Dublin",
    "Brussels",
    "Amsterdam",
    "Copenhagen",
    "Stockholm",
    "Oslo",
    "Helsinki",
    "Bern",
    "Luxembourg",
    "Monaco",
    "Andorra la Vella",
    "San Marino",
    "Reykjavik",
    "Ankara",
    "Moscow",
    "Kyiv",
    "Chisinau",
    "Tirana",
    "Skopje",
    "Podgorica",
    "Sarajevo",
    "Valletta",
    "Vilnius",
    "Riga",
    "Tallinn",
    "Washington",
    "Ottawa",
    "Mexico City",
    "Brasilia",
    "Buenos Aires",
    "Santiago",
    "Lima",
    "Bogota",
    "Caracas",
    "Quito",
    "Asuncion",
    "Montevideo",
    "Tokyo",
    "Beijing",
    "Seoul",
    "Bangkok",
    "Hanoi",
    "Jakarta",
    "Manila",
    "Kuala Lumpur",
    "Singapore",
    "New Delhi",
    "Islamabad",
    "Kabul",
    "Tehran",
    "Baghdad",
    "Riyadh",
    "Abu Dhabi",
    "Doha",
    "Kuwait City",
    "Muscat",
    "Jerusalem",
    "Amman",
    "Beirut",
    "Cairo",
    "Algiers",
    "Tunis",
    "Rabat",
    "Tripoli",
    "Khartoum",
    "Addis Ababa",
    "Nairobi",
    "Kampala",
    "Dar es Salaam",
    "Kigali",
    "Bujumbura",
    "Kinshasa",
    "Brazzaville",
    "Luanda",
    "Yaoundé",
    "Abuja",
    "Accra",
    "Dakar",
    "Bamako",
    "Niamey",
    "N'Djamena",
    "Porto-Novo",
    "Yamoussoukro",
    "Pretoria",
    "Cape Town",
    "Harare",
    "Lusaka",
    "Maputo",
    "Gaborone",
    "Windhoek",
    "Canberra",
    "Wellington",
]

CONTINENT_NAMES = {
    "AF": "Africa",
    "AS": "Asia",
    "EU": "Europe",
    "NA": "North America",
    "SA": "South America",
    "OC": "Oceania",
    "AQ": "Antarctica",
}

SPECIAL_COUNTRY_CODE_FIXES = {
    "XK": "EU",
}


def country_code_to_continent(country_code: str):
    if not country_code:
        return None

    code = country_code.upper().strip()

    if code in SPECIAL_COUNTRY_CODE_FIXES:
        return CONTINENT_NAMES.get(SPECIAL_COUNTRY_CODE_FIXES[code])

    try:
        continent_code = pc.country_alpha2_to_continent_code(code)
        return CONTINENT_NAMES.get(continent_code)
    except Exception:
        return None


def request_with_retry(url: str, params: dict, timeout: int):
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)

            if response.status_code == 429:
                wait_seconds = min(10 * attempt, 60)
                print(f"   Too Many Requests. Aștept {wait_seconds} secunde și reîncerc...")
                time.sleep(wait_seconds)
                continue

            response.raise_for_status()
            return response

        except requests.RequestException as e:
            last_error = e
            wait_seconds = min(5 * attempt, 30)
            print(f"   Eroare request (încercarea {attempt}/{MAX_RETRIES}): {e}")
            print(f"   Aștept {wait_seconds} secunde și reîncerc...")
            time.sleep(wait_seconds)

    if last_error is not None:
        raise last_error

    raise RuntimeError("Prea multe cereri către API. Nu s-a putut obține răspuns valid.")


def geocode_city(city: str, country: str):
    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json",
    }

    r = request_with_retry(GEOCODE_URL, params=params, timeout=30)
    data = r.json()

    results = data.get("results", [])
    if not results:
        return None

    best = results[0]
    country_code = best.get("country_code")
    continent = country_code_to_continent(country_code)

    return {
        "latitude": best["latitude"],
        "longitude": best["longitude"],
        "country": best.get("country", country),
        "country_code": country_code,
        "continent": continent,
    }


def fetch_weather(lat: float, lon: float):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
            "weather_code",
        ]),
        "timezone": "auto",
    }

    r = request_with_retry(WEATHER_URL, params=params, timeout=90)
    return r.json()


def build_rows(entity: str, capital: str, resolved_country: str, continent: str, weather_json: dict):
    hourly = weather_json.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    humidity = hourly.get("relative_humidity_2m", [])
    precip = hourly.get("precipitation", [])
    wind = hourly.get("wind_speed_10m", [])
    codes = hourly.get("weather_code", [])

    rows = []

    for i, ts in enumerate(times):
        if "T12:00" not in ts:
            continue

        date_part, hour_part = ts.split("T")
        hour_value = int(hour_part.split(":")[0])

        rows.append({
            "city": capital,
            "country": resolved_country,
            "entity": entity,
            "continent": continent,
            "date_record": date_part,
            "hour_record": hour_value,
            "temperature_avg": temps[i] if i < len(temps) else None,
            "temperature_min": temps[i] if i < len(temps) else None,
            "temperature_max": temps[i] if i < len(temps) else None,
            "humidity": humidity[i] if i < len(humidity) else None,
            "precipitation": precip[i] if i < len(precip) else None,
            "wind_speed": wind[i] if i < len(wind) else None,
            "weather_code": codes[i] if i < len(codes) else None,
        })

    return rows


def prioritize_capitals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["capital_norm"] = df["capital"].astype(str).str.strip()

    priority_df = df[df["capital_norm"].isin(PRIORITY_CAPITALS)].copy()
    rest_df = df[~df["capital_norm"].isin(PRIORITY_CAPITALS)].copy()

    priority_df["priority_order"] = priority_df["capital_norm"].apply(
        lambda x: PRIORITY_CAPITALS.index(x)
    )
    priority_df = priority_df.sort_values("priority_order")

    final_df = pd.concat([priority_df, rest_df], ignore_index=True)
    final_df = final_df.drop_duplicates(subset=["capital_norm"], keep="first")

    return final_df.drop(columns=["capital_norm"] + (["priority_order"] if "priority_order" in final_df.columns else []), errors="ignore")


def main():
    capitals_df = pd.read_csv(INPUT_FILE)
    capitals_df = prioritize_capitals(capitals_df).head(MAX_CAPITALS)

    all_rows = []

    for idx, row in capitals_df.iterrows():
        entity = str(row["entity"]).strip()
        capital = str(row["capital"]).strip()

        print(f"[{idx + 1}/{len(capitals_df)}] {capital} - {entity}")

        try:
            geo = geocode_city(capital, entity)
            if not geo:
                print(f"   Nu am găsit coordonate pentru {capital}")
                continue

            weather = fetch_weather(geo["latitude"], geo["longitude"])

            rows = build_rows(
                entity=entity,
                capital=capital,
                resolved_country=geo["country"],
                continent=geo["continent"],
                weather_json=weather,
            )
            all_rows.extend(rows)

            time.sleep(REQUEST_DELAY_SECONDS)

        except Exception as e:
            print(f"   Eroare la {capital}: {e}")
            time.sleep(5)

    df = pd.DataFrame(all_rows)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"Gata. S-a generat {OUTPUT_FILE} cu {len(df)} rânduri.")


if __name__ == "__main__":
    main()