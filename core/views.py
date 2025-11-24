from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import action
from django.db.models import Q
from django.db import transaction
from .models import Collection, Card, User
from .serializers import CollectionSerializer, CardSerializer, UserRegistrationSerializer, MyTokenObtainPairSerializer
from .permissions import IsOwnerOrReadOnly

class PublicCollectionsListView(generics.ListAPIView):
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Collection.objects.filter(is_public=True)\
                                 .exclude(owner=self.request.user)

class CollectionViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if self.action == 'list':
            return Collection.objects.filter(
                Q(owner=user) | Q(favorited_by=user)
            ).distinct()

        return Collection.objects.filter(is_public=True) | Collection.objects.filter(owner=user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        collection = self.get_object()
        user = request.user

        if user in collection.favorited_by.all():
            collection.favorited_by.remove(user)
            return Response({'status': 'unfavorited'})
        else:
            collection.favorited_by.add(user)
            return Response({'status': 'favorited'})

class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        allowed_collections = Collection.objects.filter(is_public=True) | Collection.objects.filter(owner=user)
        return Card.objects.filter(collection__in=allowed_collections)

    def perform_create(self, serializer):
        collection = serializer.validated_data['collection']
        if collection.owner != self.request.user:
            raise permissions.PermissionDenied("You do not have permission to add a card to this collection.")
        serializer.save()

class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)