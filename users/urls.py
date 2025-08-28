from django.urls import path

from users.views import CreateUserView, ManageUserView

app_name = "users"

urlpatterns = [
   path("register/", CreateUserView.as_view(), name="register"),
   path("me/", ManageUserView.as_view(), name="manage_user")
]
