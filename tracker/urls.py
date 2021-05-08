
from django.urls import path
from . import views, api

urlpatterns = [
    path('', views.index, name='index'),
    # path('following', views.FollowingListView.as_view(), name='following'),
    # path("profile/<int:userId>", views.ProfileListView.as_view(), name="profile"),
    path("account", views.account, name="account"),
    path("categories", views.categories, name="categories"),
    path("category/<int:id>", views.category, name="category"),
    path("reports", views.reports, name="reports"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    # Ajax API
    path("api/transaction", api.transaction, name="api-transaction"),
    path("api/category", api.category, name="api-category"),
    path("api/balance", api.balance, name="api-balance"),
]
