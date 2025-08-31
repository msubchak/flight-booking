from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from core.models import AirplaneType, Airplane, Country, City, Airport, Route, Flight, Crew, Position


def sample_route(distance=500, **params) -> Route:
    source_country, _ = Country.objects.get_or_create(name="Ukraine")
    source_city, _ = City.objects.get_or_create(name="Kyiv", country=source_country)
    source_airport, _ = Airport.objects.get_or_create(name="Boryspil", city=source_city)

    dest_country, _ = Country.objects.get_or_create(name="Poland")
    dest_city, _ = City.objects.get_or_create(name="Warsaw", country=dest_country)
    dest_airport, _ = Airport.objects.get_or_create(name="Chopin", city=dest_city)

    defaults = {
        "source": source_airport,
        "destination": dest_airport,
        "distance": distance
    }
    defaults.update(params)
    return Route.objects.create(**defaults)


def sample_crews(**params) -> Crew:
    position, _ = Position.objects.get_or_create(name="Pilot")

    defaults = {
        "first_name": "test1",
        "last_name": "test11",
        "position": position,
    }
    defaults.update(params)
    return Crew.objects.create(**defaults)


def sample_flight(**params) -> Flight:
    airplane_type, _ = AirplaneType.objects.get_or_create(name="Boeing 737")
    airplane = Airplane.objects.create(
        name="Boeing",
        rows=20,
        seats_in_row=6,
        airplane_type=airplane_type,
    )
    route = sample_route()
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


FLIGHT_URL = reverse("core:flight-list")


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(FLIGHT_URL)
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

        res = self.client.get(FLIGHT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)