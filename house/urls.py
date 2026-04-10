from django.urls import path
from .views import (HouseListCreateView, HouseDetailView, WishlistToggleView, WishlistView, MessageListCreateView,
                    RegionListView, DistrictListView, )

urlpatterns = [
    path('houses/', HouseListCreateView.as_view()),
    path('houses/<int:pk>/', HouseDetailView.as_view()),
    path('wishlist/', WishlistView.as_view()),
    path('wishlist/toggle/', WishlistToggleView.as_view()),
    path('messages/', MessageListCreateView.as_view()),
    path('regions/', RegionListView.as_view(), name='region-list'),
    path('regions/<int:region_id>/', DistrictListView.as_view(), name='district-list'),
]