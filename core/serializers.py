from rest_framework import serializers
from .models import Collection, Card, User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db import transaction

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['email'] = user.email
        return token

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'front', 'back']

class CardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['front', 'back']

class CollectionSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source='owner.email', read_only=True)
    cards = CardSerializer(many=True, read_only=True)
    cards_data = CardCreateSerializer(many=True, write_only=True, required=False)
    
    is_owner = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    favorites_count = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = [
            'id', 'owner', 'title', 'description', 'is_public', 'cards', 
            'cards_data', 'is_owner', 'is_favorited', 'favorites_count'
        ]

    def get_is_owner(self, obj):
        user = self.context['request'].user
        return obj.owner == user

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.favorited_by.filter(id=user.id).exists()
        return False

    def get_favorites_count(self, obj):
        return obj.favorited_by.count()
    
    def create(self, validated_data):
        cards = validated_data.pop('cards_data', [])
        collection = Collection.objects.create(**validated_data)
        for card_data in cards:
            Card.objects.create(collection=collection, **card_data)
        return collection

    def update(self, instance, validated_data):
        cards_data = validated_data.pop('cards_data', [])
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.is_public = validated_data.get('is_public', instance.is_public)
        instance.save()

        existing_cards = {card.id: card for card in instance.cards.all()}

        cards_to_create = []
        cards_to_update = []
        incoming_card_ids = set()

        for card_data in cards_data:
            card_id = card_data.get('id', None)
            if card_id:
                if card_id in existing_cards:
                    card_instance = existing_cards[card_id]
                    card_instance.front = card_data['front']
                    card_instance.back = card_data['back']
                    cards_to_update.append(card_instance)
                    incoming_card_ids.add(card_id)
            else:
                cards_to_create.append(
                    Card(collection=instance, front=card_data['front'], back=card_data['back'])
                )
        
        if cards_to_create:
            Card.objects.bulk_create(cards_to_create)
        
        if cards_to_update:
            Card.objects.bulk_update(cards_to_update, ['front', 'back'])
            
        ids_to_delete = set(existing_cards.keys()) - incoming_card_ids
        if ids_to_delete:
            Card.objects.filter(id__in=ids_to_delete).delete()
        return instance