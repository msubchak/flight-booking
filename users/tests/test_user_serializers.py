from django.contrib.auth import get_user_model
from django.test import TestCase

from users.serializers import UserSerializer


class UserSerializersTests(TestCase):
    def test_user_serializer_create(self):
        data = {
            "email": "test@email.com",
            "password": "password12345"
        }
        serializer = UserSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        self.assertNotEqual(user.password, data["password"])
        self.assertTrue(user.check_password(data["password"]))

    def test_user_serializer_update_password(self):
        user = get_user_model().objects.create_user(
            email="test_email.com",
            password="password12345"
        )
        serializer = UserSerializer(
            user, data={"password": "newpass"}, partial=True
        )

        self.assertTrue(serializer.is_valid())
        update_user = serializer.save()

        self.assertTrue(update_user.check_password("newpass"))

    def test_create_superuser_success(self):
        user = get_user_model().objects.create_superuser(
            email="test@email.com",
            password="password12345"
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
