from geopy.distance import geodesic
from typing import Tuple, Dict


def calculate_distance(user_coords: Tuple[float, float],
                       store_coords: Tuple[float, float]) -> Dict:
    """Masofani hisoblash va natijani qaytarish"""
    distance_km = geodesic(user_coords, store_coords).kilometers
    distance_m = distance_km * 1000

    # Taxminiy vaqt hisoblash
    car_time_hours = distance_km / 60  # 60 km/soat tezlikda
    walk_time_hours = distance_km / 5  # 5 km/soat piyoda

    return {
        'km': round(distance_km, 2),
        'meters': round(distance_m, 0),
        'car_time_minutes': round(car_time_hours * 60, 1),
        'walk_time_minutes': round(walk_time_hours * 60, 1)
    }


def find_nearest_store(user_coords: Tuple[float, float],
                       stores: Dict) -> Tuple[str, Dict]:
    """Eng yaqin do'koni topish"""
    nearest_store = None
    min_distance = float('inf')
    distances = {}

    for store_name, store_data in stores.items():
        distance = calculate_distance(user_coords, store_data['location'])
        distances[store_name] = distance

        if distance['km'] < min_distance:
            min_distance = distance['km']
            nearest_store = store_name

    return nearest_store, distances