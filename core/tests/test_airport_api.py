import uuid
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import F, Count
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from core.models import AirplaneType, Airplane, Country, City, Airport, Route, Flight, Crew, Position
from core.serializers import FlightListSerializer, FlightRetrieveSerializer, CrewListSerializer, CrewSerializer, \
    PositionSerializer


def sample_route(
        distance=500,
        source_city_name="Kyiv",
        dest_city_name="Warsaw",
        **params
) -> Route:
    source_country, _ = Country.objects.get_or_create(name="Ukraine")
    source_city, _ = City.objects.get_or_create(name=source_city_name, country=source_country)
    source_airport, _ = Airport.objects.get_or_create(name=f"{source_city_name} Airport", city=source_city)

    dest_country, _ = Country.objects.get_or_create(name="Poland")
    dest_city, _ = City.objects.get_or_create(name=dest_city_name, country=dest_country)
    dest_airport, _ = Airport.objects.get_or_create(name=f"{dest_city_name} Airport", city=dest_city)

    defaults = {
        "source": source_airport,
        "destination": dest_airport,
        "distance": distance
    }

    defaults.update(params)

    route, _ = Route.objects.get_or_create(
        source=defaults["source"],
        destination=defaults["destination"],
        defaults={"distance": defaults["distance"]}
    )
    return route


def sample_crews(**params) -> Crew:
    position, _ = Position.objects.get_or_create(name="Pilot")

    defaults = {
        "first_name": "test1",
        "last_name": "test11",
        "position": position,
    }
    defaults.update(params)
    return Crew.objects.create(**defaults)


def sample_flight(route_params=None, **params) -> Flight:
    airplane_type, _ = AirplaneType.objects.get_or_create(name="Boeing 737")
    airplane = Airplane.objects.create(
        name=f"Boeing-{uuid.uuid4()}",
        rows=20,
        seats_in_row=6,
        airplane_type=airplane_type,
    )

    if route_params is None:
        route_params = {}

    route = sample_route(**route_params)
    crew = sample_crews()

    defaults = {
        "route": route,
        "airplane": airplane,
        "departure_time": datetime(2025, 12, 1, 7, 0),
        "arrival_time": datetime(2025, 12, 2, 8, 0),
    }
    defaults.update(params)
    flight = Flight.objects.create(**defaults)
    flight.crews.add(crew)
    return flight


FLIGHT_LIST_URL = reverse("core:flight-list")
CREW_LIST_URL = reverse("core:crew-list")
POSITION_LIST_URL = reverse("core:position-list")


def flight_detail_url(flight_id):
    return reverse("core:flight-detail", args=[flight_id])


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_flight_list_auth_required(self):
        res = self.client.get(FLIGHT_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_flight_retrieve_auth_required(self):
        flight = sample_flight()
        res = self.client.get(flight_detail_url(flight.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="12345",
        )
        self.client.force_authenticate(self.user)

    def test_flight_list(self):
        sample_flight()

        res = self.client.get(FLIGHT_LIST_URL)
        flights = Flight.objects.annotate(
            tickets_available=F("airplane__seats_in_row") * F("airplane__rows") - Count("tickets", distinct=True),
            crew_count=Count("crews", distinct=True),
        )
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_flights_list_by_departure_city(self):
        flight_1 = sample_flight(route_params={"source_city_name": "Kyiv", "dest_city_name": "London"})
        flight_2 = sample_flight(route_params={"source_city_name": "Lviv", "dest_city_name": "Berlin"})
        res = self.client.get(
            FLIGHT_LIST_URL,
            data={
                "departure_city": "Kyiv"
            }
        )
        serializer_kyiv = FlightListSerializer(Flight.objects.filter(id=flight_1.id).annotate(
            tickets_available=F("airplane__seats_in_row") * F("airplane__rows") - Count("tickets", distinct=True),
            crew_count=Count("crews", distinct=True)
        ),
            many=True
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer_kyiv.data)

    def test_filter_flights_list_by_arrival_city(self):
        flight_1 = sample_flight(route_params={"source_city_name": "London", "dest_city_name": "Kyiv"})
        flight_2 = sample_flight(route_params={"source_city_name": "Lviv", "dest_city_name": "Berlin"})
        res = self.client.get(
            FLIGHT_LIST_URL,
            data={
                "arrival_city": "Kyiv"
            }
        )
        serializer_kyiv = FlightListSerializer(Flight.objects.filter(id=flight_1.id).annotate(
            tickets_available=F("airplane__seats_in_row") * F("airplane__rows") - Count("tickets", distinct=True),
            crew_count=Count("crews", distinct=True)
        ),
            many=True
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer_kyiv.data)

    def test_filter_flights_list_by_departure_time(self):
            flight_1 = sample_flight(departure_time=datetime(2020, 12, 1, 7, 0))
            flight_2 = sample_flight(departure_time=datetime(2023, 5, 1, 7, 0))
            flight_3 = sample_flight(departure_time=datetime(2025, 3, 1, 7, 0))

            res = self.client.get(
                FLIGHT_LIST_URL,
                data={
                    "departure_date": flight_1.departure_time.date().isoformat()
                }
            )
            serializer = FlightListSerializer(Flight.objects.filter(departure_time__date=flight_1.departure_time.date()).annotate(
            tickets_available=F("airplane__seats_in_row") * F("airplane__rows") - Count("tickets", distinct=True),
            crew_count=Count("crews", distinct=True)
        ),
            many=True
        )

            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data["results"], serializer.data)

    def test_filter_flights_list_by_arrival_time(self):
        flight_1 = sample_flight(arrival_time=datetime(2020, 12, 1, 7, 0))
        flight_2 = sample_flight(arrival_time=datetime(2023, 5, 1, 7, 0))
        flight_3 = sample_flight(arrival_time=datetime(2025, 3, 1, 7, 0))

        res = self.client.get(
            FLIGHT_LIST_URL,
            data={
                "arrival_date": flight_1.arrival_time.date().isoformat()
            }
        )
        serializer = FlightListSerializer(Flight.objects.filter(arrival_time__date=flight_1.arrival_time.date()).annotate(
            tickets_available=F("airplane__seats_in_row") * F("airplane__rows") - Count("tickets", distinct=True),
            crew_count=Count("crews", distinct=True)
        ),
            many=True
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)


    def test_create_flight_list_forbidden(self):
        flight = sample_flight()
        payload = FlightListSerializer(flight).data
        res = self.client.post(FLIGHT_LIST_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_flight_retrieve(self):
        flight = sample_flight()

        res = self.client.get(flight_detail_url(flight.id))
        flights = Flight.objects.annotate(
            tickets_available=F("airplane__seats_in_row") * F("airplane__rows") - Count("tickets", distinct=True),
            crew_count=Count("crews", distinct=True),
        )
        flight_obj = Flight.objects.get(id=flight.id)
        serializer = FlightRetrieveSerializer(flight_obj)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_flight_retrieve_forbidden(self):
        flight = sample_flight()
        payload = FlightRetrieveSerializer(flight).data
        res = self.client.post(flight_detail_url(flight.id), payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_flight_retrieve_not_found(self):
        fake_id = 999
        res = self.client.get(flight_detail_url(fake_id))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class UnauthenticatedCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_crew_auth_required(self):
        res = self.client.get(CREW_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="12345",
        )
        self.client.force_authenticate(self.user)

    def test_crew(self):
        crew_1 = sample_crews()
        crew_2 = sample_crews()
        crews = [crew_1, crew_2]

        res = self.client.get(CREW_LIST_URL)
        serializer = CrewListSerializer(crews, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_crew_by_position(self):
        crew_1 = sample_crews()
        crew_2 = sample_crews()
        res = self.client.get(
            CREW_LIST_URL,
            data={
                "position": "pilot"
            }
        )
        crews = Crew.objects.filter(position__name__icontains="pilot")
        serializer = CrewListSerializer(crews, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_crew_forbidden(self):
        crew = sample_crews()
        payload = CrewListSerializer(crew).data
        res = self.client.post(CREW_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class UnauthenticatedPositionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_position_auth_required(self):
        res = self.client.get(POSITION_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPositionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="12345",
        )
        self.client.force_authenticate(self.user)

    def test_position(self):
        position_1 = Position.objects.create(name="test1")
        position_2 = Position.objects.create(name="test2")
        positions = [position_1, position_2]
        res = self.client.get(POSITION_LIST_URL)
        serializer = PositionSerializer(positions, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_position_forbidden(self):
        position = Position.objects.create(name="test")
        payload = PositionSerializer(position).data
        res = self.client.post(POSITION_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

