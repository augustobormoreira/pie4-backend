from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager( BaseUserManager ):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('o email não foi fornecido')
        
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()

        return user
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('superuser must have is_staff = True')

        if not extra_fields.get('is_superuser'):
            raise ValueError('superuser must have is_superuser = True')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    objects = UserManager()

    def __str__(self):
        return self.first_name

    def has_module_perms(self, app_label):
        return True
    
    def has_perm(self, perm, obj=None):
        return True

class Collection(models.Model):
    owner = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='collections')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=False)
    favorited_by = models.ManyToManyField('core.User', related_name='favorite_collections', blank=True)

    def __str__(self):
        return f'{self.title} by {self.owner.email}'

class Card(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='cards')
    front = models.TextField()
    back = models.TextField()

    def __str__(self):
        return f'Card "{self.front[:20]}..." in "{self.collection.title}"'