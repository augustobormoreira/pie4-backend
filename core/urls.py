from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CollectionViewSet, CardViewSet, PublicCollectionsListView

router = DefaultRouter()
router.register(r'collections', CollectionViewSet, basename='collection')
router.register(r'cards', CardViewSet, basename='card')

urlpatterns = [
    path('', include(router.urls)),
    path('public-collections/', PublicCollectionsListView.as_view(), name='public-collections-list'),
]